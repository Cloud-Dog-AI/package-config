from cloud_dog_config import __version__


def test_public_version_export_matches_package_release() -> None:
    assert __version__ == "0.3.4"
