from smokestack.aws import endeavor
from botocore.exceptions import ClientError
from mock import Mock, patch

def test_endeavor__throttled() -> None:
    with patch("smokestack.aws.sleep") as sleep:
        endeavor(
            Mock(side_effect=[
                ClientError(error_response={},
                operation_name="throttled"),
                None,
            ])
        )
    sleep.assert_called_once_with(8)
