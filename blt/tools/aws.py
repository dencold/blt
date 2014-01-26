"""
Toolset module for AWS using blt.

Currently, the primary use case is access to the Amazon Simple Storage Service
(`S3 <http://aws.amazon.com/s3/>`_) through the
`boto api <http://boto.s3.amazonaws.com/ref/s3.html>`_. More functionality
may be added down the road for other AWS services.

Author: @dencold (Dennis Coldwell)
"""
import gzip
import hashlib
import mimetypes
import os
from StringIO import StringIO
# from jsmin import *
# from cssmin import *

# boto may not be available before initializing requirements, just ignore
# the exception in that case.
try:
    import boto
except ImportError:
    pass

from blt.environment import Commander
from blt.helpers import local

# The list of content types to gzip, add more if needed
COMPRESSIBLE = [ 'text/plain', 'text/csv', 'application/xml',
                'application/javascript', 'text/css' ]

class AmazonCommands(Commander):
    """
    Commander class for wrapping a CLI to Amazon Web Services (AWS).

    Exposes general push/pull and listing functionality to S3 buckets. The
    class authenticates with AWS using the AWS_ACCESS_KEY_ID and
    AWS_SECRET_ACCESS_KEY configuration settings from blt.
    """

    def sync_s3(self, source_folder=None, prefix=None):
        """
        Pushes files from a given source folder to an AWS S3 bucket.

        This is the main workhorse for the S3 blt toolchain, it will sync up
        a given source folder and push any deltas to the S3 bucket. In order to
        determine which files have changed, the command makes use of boto's md5
        to compare hashes. Once it has a changeset, it follows these steps:

        * determines if the file is compressible, and if so, gzips.
        * figures out the files mimetype
        * adds headers and permissions

        It will then upload it directly to the S3 bucket that was configured
        in the beltenv file.

        Args:
            source_folder: a string representing the path of the folder to sync
                files from. example: '/Users/coldwd/static_files/'
            prefix: the root folder within the S3 bucket to push to. For
                example, we could be pushing to the "matter-developers" S3
                bucket, but we want to isolate to a specific subdirectory like
                "dencold". In this case we would pass a prefix of "dencold/"
        Usage:
            blt e:[env] aws.sync_s3 [source_folder] [prefix]

        Examples:
            blt e:s aws.sync_s3 - default uses config settings
            blt e:s aws.sync_s3 /Users/coldwd/my_dir - uses runtime source_folder
            blt e:s aws.sync_s3 /Users/coldwd/my_dir dencold/ - uses runtime
                source_folder and prefix
        """
        config = self._get_config(source_folder, prefix)

        file_hashes = get_hashes_from_dirtree(config['source_folder'])
        s3_hashes = get_hashes_from_s3bucket(config['bucket'], config['prefix'])

        namelist = get_changed_files(file_hashes, s3_hashes)

        for name in namelist:
            upload_file(config['source_folder'],
                name,
                config['bucket'],
                config['prefix'])

        print '%d files uploaded to bucket %s' % (len(namelist),
            config['bucket'].name)

    def pull_s3(self, source_folder=None, prefix=None):
        """
        Pulls files from an AWS S3 bucket to a given source folder.

        The logic is the same as ``sync_s3``, just in reverse.

        Args:
            source_folder: a string representing the path of the folder to sync
                files to.
            prefix: the root folder within the S3 bucket to pull from.

        Usage:
            blt e:[env] aws.pull_s3 [source_folder] [prefix]

        Examples:
            blt e:s aws.pull_s3 - default uses config settings
            blt e:s aws.pull_s3 /Users/coldwd/my_dir - uses runtime source_folder
            blt e:s aws.pull_s3 /Users/coldwd/my_dir dencold/ - uses runtime
                source_folder and prefix
        """
        config = self._get_config(source_folder, prefix)

        file_hashes = get_hashes_from_dirtree(config['source_folder'])
        s3_hashes = get_hashes_from_s3bucket(config['bucket'], config['prefix'])

        namelist = get_changed_files(s3_hashes, file_hashes)

        for name in namelist:
            prep_path(os.path.join(config['source_folder'], name))

            download_file(config['source_folder'],
                name,
                s3_hashes[name]['s3_key'],
                s3_hashes[name]['is_compressed'])

    def list_s3(self, prefix=None):
        """
        Lists all files in the S3 bucket.

        Args:
            prefix: the root folder within the S3 bucket to list.

        Usage:
            blt e:[env] aws.list_s3 [prefix]

        Examples:
            blt e:s aws.list_s3 - default
            blt e:s aws.list_s3 dencold/ - uses runtime prefix
        """
        config = self._get_config(prefix=prefix)

        for asset in config['bucket'].list(prefix=config['prefix']):
            print "- %s" % asset

    def list_changes(self, source_folder=None, prefix=None):
        """
        Lists changed files between the source folder and S3 bucket.

        The command compares md5 hashes between source & target to determine
        the list of deltas.  It prints the result to stdout.

        Args:
            source_folder: a string representing the path of the folder to
                compare files from. if None, we will pull from blt config.
            prefix: the root folder within the S3 bucket to compare. if None,
                we default to an empty string ''.

        Usage:
            blt e:[env] aws.list_changes [source_folder] [prefix]

        Examples:
            blt e:s aws.list_changes - default uses config settings
            blt e:s aws.list_changes /Users/coldwd/my_dir - uses runtime source_folder
            blt e:s aws.list_changes /Users/coldwd/my_dir dencold/ - uses
                runtime source_folder and prefix
        """
        config = self._get_config(source_folder, prefix)

        file_hashes = get_hashes_from_dirtree(config['source_folder'])
        s3_hashes = get_hashes_from_s3bucket(config['bucket'], config['prefix'])

        for f in get_changed_files(file_hashes, s3_hashes):
            print "- %s" % f

    def _get_config(self, source_folder=None, prefix=None):
        """
        Populates a config dict for access to AWS.

        This function handles the upfront work to determine AWS credentials,
        bucket details, prefixes, etc. that are required for transmission to
        S3.

        Args:
            source_folder: a string representing the path of the folder to sync
                files from. if None, we will pull from blt config.
            prefix: the root folder within the S3 bucket to push to. if None,
                we default to an empty string ''.

        Returns:
            A dict that maps the required config elements:
                * bucket
                * source_folder
                * prefix
        """
        ret_dict = dict()

        ret_dict['bucket'] = self._get_s3_bucket()
        ret_dict['source_folder'] = self._get_source_folder(source_folder)
        ret_dict['prefix'] = self._get_folder_prefix(prefix)

        return ret_dict

    def _get_s3_bucket(self):
        """
        Retrieves the S3 bucket from the blt config file.

        Returns:
            A boto S3 bucket object.
        """
        AWS_ACCESS_KEY_ID = self.cfg['aws']['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = self.cfg['aws']['AWS_SECRET_ACCESS_KEY']
        conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        return conn.get_bucket(self.cfg['aws']['AWS_BUCKET_NAME'])

    def _get_folder_prefix(self, prefix=None):
        """
        Determines the folder prefix for the S3 bucket.

        Order of preference for the prefix is:
            1) if given, we use the argument passed as prefix.
            2) if no argument, we try to see if the AWS_FOLDER_PREFIX is
               configured on blt configuration file and use if available.
            3) default is an empty string if first two are not found.

        Args:
            prefix: the root folder within the S3 bucket. default is an empty
                string ''.

        Returns:
            a string representing the root folder prefix.
        """
        if prefix:
            return prefix

        if 'AWS_FOLDER_PREFIX' in self.cfg['aws']:
            return self.cfg['aws']['AWS_FOLDER_PREFIX']
        else:
            return ''

    def _get_source_folder(self, folder=None):
        """
        Determines the source folder on the local filesystem.

        We either use the passed folder from the command line, or default to
        the SOURCE_FOLDER configuration setting on bltenv.

        Args:
            source_folder: optional string for the path of the folder.

        Returns:
            A string representing the source folder.
        """
        return folder if folder else self.cfg['aws']['SOURCE_FOLDER']

def compute_md5(filename, block_size=2**20):
    md5 = hashlib.md5()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()

def get_hashes_from_dirtree(src_folder):
    ret = dict()
    for root, dirs, files in os.walk(src_folder):
        if files and not '.webassets-cache' in root:
            path = os.path.relpath(root, src_folder)

            for f in files:
                name = os.path.normpath(os.path.join(path, f))

                # skip any files with a resource fork (such as Icon\r)
                if name.endswith('\r'):
                    continue

                # aws only provides md5 hashes in their boto api, let's
                # calculate our local md5 and compare to see if anything
                # has changed
                local_md5 = compute_md5(os.path.join(src_folder, name))

                ret[name] = {'file_path': os.path.join(src_folder, name),
                            'hash': local_md5}

    return ret

def get_hashes_from_s3bucket(bucket, prefix=''):
    ret = dict()
    for key in bucket.list(prefix=prefix):
        compressed = False

        # ignore Icon files, they have a resource fork that screws things up
        if os.path.basename(key.key) in ['Icon\n']:
            continue

        # [dmc] boto is really really shitty.  the iterated keys coming from
        # bucket.list do not include metadata (whereas if you issue a
        # bucket.get_key() you *do* get your metadata) extremely frustrating
        # we do a hack to figure out if this is likely to be compressible
        # data and then pull the key directly to avoid this.  blarg.
        # more info on the failings of bucket.list:
        # https://github.com/boto/boto/blob/2.9.1/boto/s3/bucket.py#L228
        filetype, encoding = mimetypes.guess_type(key.key)
        if filetype in COMPRESSIBLE:

            # explicity get the key so we can get at metadata
            md_key = bucket.get_key(key.key)
            if is_key_compressed(md_key):
                key_md5 = md_key.get_metadata('uncompressed_md5')
                compressed = True
            else:
                key_md5 = key.etag.strip('"')
        else:
            # note that the HTTP ETag standard requires a quoted
            # value.  our local md5 is not quoted, this is why we
            # are explicitly stripping quotes below.
            key_md5 = key.etag.strip('"')

        dict_key = handle_prefix(key.key, prefix)
        ret[dict_key] = {
            's3_key': key,
            'hash': key_md5,
            'is_compressed': compressed
        }

    return ret

def handle_prefix(path, prefix):
    if prefix:
        # we must remove prefix from our key so we can properly compare
        # with source.
        first, sep, last = path.partition(prefix)
        if last:
            return last.lstrip('/')
    else:
        return path

def get_changed_files(src_hashes, target_hashes):
    namelist = []
    src_keyset = set(src_hashes.keys())
    target_keyset = set(target_hashes.keys())

    # automatically add any files that are in source and not in target:
    namelist += src_keyset.difference(target_keyset)

    # for those keys that *are* in target, we need to compare hashcodes
    for key in src_keyset.intersection(target_keyset):
        if src_hashes[key]['hash'] != target_hashes[key]['hash']:
            namelist.append(key)

    return namelist

def is_key_compressed(key):
    return key.get_metadata('gzipped') == 'true'

def compress_and_upload(key, filename, headers):
    compressed = StringIO()
    headers['Content-Encoding'] = 'gzip'

    with open(filename, 'r') as f_in:
        gz = gzip.GzipFile(fileobj=compressed, mode='wb')
        gz.writelines(f_in)
        gz.close()

    key.set_metadata('gzipped', 'true')
    key.set_metadata('uncompressed_md5', compute_md5(filename))
    key.set_contents_from_string(compressed.getvalue(), headers)

def upload_file(source_folder, name, bucket, prefix=''):
    filetype, encoding = mimetypes.guess_type(name)
    filetype = filetype or 'application/octet-stream'
    headers = { 'Content-Type': filetype, 'x-amz-acl': 'public-read' }
    states = [filetype]

    # TODO, come back to revisit this.  we may want to start doing minification
    # within blt as well as set expiry headers.
    # if options.expires:
    #     # We only use HTTP 1.1 headers because they are relative to the time of download
    #     # instead of being hardcoded.
    #     headers['Cache-Control'] = 'max-age %d' % (3600 * 24 * 365)

    # if options.minify and filetype == 'application/javascript':
    #     outs = StringIO()
    #     JavascriptMinify().minify(content, outs)
    #     content.close()
    #     content = outs.getvalue()
    #     if len(content) &gt; 0 and content[0] == '\n':
    #         content = content[1:]
    #     content = BytesIO(content)
    #     states.append('minified')

    # if options.minify and filetype == 'text/css':
    #     outs = cssmin(content.read())
    #     content.close()
    #     content = outs
    #     if len(content) &gt; 0 and content[0] == '\n':
    #         content = content[1:]
    #     content = BytesIO(content)
    #     states.append('minified')

    key = bucket.new_key(prefix + name)
    filename = os.path.join(source_folder, name)

    if filetype in COMPRESSIBLE:
        states.append('gzipped')
        compress_and_upload(key, filename, headers)
    else:
        with open(filename, 'rb') as f:
            key.set_contents_from_file(f, headers)

    states = ', '.join(states)
    print '- %s (%s)' % (name, states)

def download_file(source_folder, name, key, compressed):
    path = os.path.join(source_folder, name)

    if compressed:
        filestr = StringIO(key.get_contents_as_string())
        with open(path, 'w') as fileptr:
            gz = gzip.GzipFile(fileobj=filestr, mode='rb')
            file_content = gz.read()
            fileptr.write(file_content)
            gz.close()

        print 'downloaded: %s' % name
    elif os.path.basename(path):
        with open(path, 'w') as fileptr:
            key.get_contents_to_file(fileptr)

        print 'downloaded: %s' % name

def prep_path(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.isdir(dirname):
        try:
            os.makedirs(dirname)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and path.isdir(dir):
                pass
            else:
                raise
