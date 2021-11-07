from typing import Dict, List
from boto3.session import Session

SystemsManagerParameters = Dict[str, str]

def get_parameters(names: List[str], session: Session) -> SystemsManagerParameters:
    ssm = session.client("ssm")
    response = ssm.get_parameters(Names=names)
    return { k.get("Name", ""): k.get("Value", "") for k in response["Parameters"]  }
