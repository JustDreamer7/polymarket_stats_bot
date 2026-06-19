import zipfile
from io import BytesIO


def extract_zip_member(zip_bytes: bytes, member_name: str) -> str:
    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        with archive.open(member_name) as member:
            return member.read().decode("utf-8")
