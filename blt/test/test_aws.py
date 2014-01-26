import pytest
from mock import patch, call, Mock, MagicMock

from blt.tools import aws

@pytest.fixture
def cmds():
    config = {
       "aws": {
           "AWS_ACCESS_KEY_ID": "JLKSNLBNLSKDFJWOEI"
         , "AWS_SECRET_ACCESS_KEY": "JFvnwoaifeIOJFnegoiwfaqEF"
         , "AWS_BUCKET_NAME": "matter-developers"
         , "SOURCE_FOLDER": "/Users/coldwd/data/pubweb/static_assets/"
         , "AWS_FOLDER_PREFIX": "dencold/"
        }
    }

    return aws.AmazonCommands(config)

@pytest.fixture
def source_hashes():
    return {
        'images/same_hash.jpg': {'hash': '7f7b682a6da0ffb6f40811ffba10ade3'},
        'images/diff_hash.jpg': {'hash': 'bdba7bf1340ceddb3e3c3aa3cd7d0ad6'},
        'images/dne.jpg': {'hash': 'b68a0e1dd8afc98bc883c3cf11b73526'}
    }

@pytest.fixture
def target_hashes():
    return {
        'images/same_hash.jpg': {'hash': '7f7b682a6da0ffb6f40811ffba10ade3'},
        'images/diff_hash.jpg': {'hash': '2f2a916dfbe711ab85b98ef2da41969c'},
        'images/only_target.jpg': {'hash': '6a410bc526acad08999c398c82882bd4'}
    }
# -- Setup/Teardown -----------------------------------------------------------

# Setup Module-wide mocks
aws.local = Mock()
aws.boto = Mock()

def teardown_function(function):
    """this is called after every test case runs"""
    aws.local.reset_mock()
    aws.boto.reset_mock()

# -- Test Cases! --------------------------------------------------------------
def test_sync_s3(cmds):
    # setup mocks
    cmds._get_s3_bucket = Mock()
    bucket = Mock()
    cmds._get_s3_bucket.return_value = bucket

    # these need to be switched to patches...they affect *all* test methods
    aws.get_hashes_from_dirtree = Mock(return_value=source_hashes())
    aws.get_hashes_from_s3bucket = Mock(return_value=target_hashes())
    aws.upload_file = Mock()

    cmds.sync_s3()
    calls = [
        call('/Users/coldwd/data/pubweb/static_assets/'
            , 'images/dne.jpg'
            , bucket
            , 'dencold/'),
        call('/Users/coldwd/data/pubweb/static_assets/'
            , 'images/diff_hash.jpg'
            , bucket
            , 'dencold/')
    ]

    assert len(aws.upload_file.mock_calls) == 2
    aws.upload_file.assert_has_calls(calls)

def test_get_changed_files(source_hashes, target_hashes):
    changed_files = aws.get_changed_files(source_hashes, target_hashes)

    assert sorted(changed_files) == [ 'images/diff_hash.jpg', 'images/dne.jpg']


