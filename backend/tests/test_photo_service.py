"""Service tests for profile photo upload/delete use cases."""

from pathlib import Path

import pytest

from app.models.enums import MediaModerationStatus
from app.repositories.identity import IdentityRepository
from app.storage.local import LocalPhotoStorage
from app.use_cases.delete_profile_photo import (
    DeleteProfilePhotoUseCase,
    PhotoNotFoundError,
)
from app.use_cases.get_my_profile import UserNotFoundError
from app.use_cases.upload_profile_photo import (
    PhotoUploadError,
    UploadProfilePhotoUseCase,
)
from tests.conftest import create_user

PNG_CONTENT = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def make_upload_use_case(session, root: Path) -> UploadProfilePhotoUseCase:
    return UploadProfilePhotoUseCase(
        IdentityRepository(session),
        LocalPhotoStorage(root, media_base_url="http://test"),
        max_upload_bytes=1024,
        auto_approve=True,
    )


def make_delete_use_case(session) -> DeleteProfilePhotoUseCase:
    return DeleteProfilePhotoUseCase(IdentityRepository(session))


async def test_upload_assigns_incrementing_positions(db_session, tmp_path):
    user_id = await create_user(db_session, verified=False)
    use_case = make_upload_use_case(db_session, tmp_path)

    first = await use_case.execute(user_id=user_id, filename="a.png", content=PNG_CONTENT)
    second = await use_case.execute(user_id=user_id, filename="b.jpg", content=PNG_CONTENT)

    assert [p.position for p in first.photos] == [1]
    assert [p.position for p in second.photos] == [1, 2]
    assert second.photos[0].moderationStatus == MediaModerationStatus.APPROVED
    assert second.photos[0].url.startswith("http://test/media/")
    assert second.verification == {"isVerified": True}
    assert len(list(tmp_path.iterdir())) == 1


async def test_upload_writes_file_to_storage(db_session, tmp_path):
    user_id = await create_user(db_session)
    use_case = make_upload_use_case(db_session, tmp_path)

    result = await use_case.execute(user_id=user_id, filename="selfie.png", content=PNG_CONTENT)

    key = await IdentityRepository(db_session).get_photo(result.photos[0].id)
    assert key is not None
    assert LocalPhotoStorage(tmp_path).open(key.storage_key) == PNG_CONTENT


async def test_upload_rejects_large_file(db_session, tmp_path):
    user_id = await create_user(db_session)
    use_case = make_upload_use_case(db_session, tmp_path)

    with pytest.raises(PhotoUploadError):
        await use_case.execute(user_id=user_id, filename="big.png", content=b"1" * 2048)


async def test_upload_rejects_non_image_extension(db_session, tmp_path):
    user_id = await create_user(db_session)
    use_case = make_upload_use_case(db_session, tmp_path)

    with pytest.raises(PhotoUploadError):
        await use_case.execute(user_id=user_id, filename="notes.txt", content=b"hello")


async def test_upload_unknown_user_raises(db_session, tmp_path):
    use_case = make_upload_use_case(db_session, tmp_path)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(user_id="missing", filename="a.png", content=PNG_CONTENT)


async def test_delete_soft_deletes_photo(db_session, tmp_path):
    user_id = await create_user(db_session)
    upload = make_upload_use_case(db_session, tmp_path)
    result = await upload.execute(user_id=user_id, filename="a.png", content=PNG_CONTENT)
    photo_id = result.photos[0].id

    after_delete = await make_delete_use_case(db_session).execute(
        user_id=user_id, photo_id=photo_id
    )

    assert after_delete.photos == []
    photo = await IdentityRepository(db_session).get_photo(photo_id)
    assert photo.deleted_at is not None


async def test_delete_foreign_photo_raises(db_session, tmp_path):
    owner_id = await create_user(db_session)
    upload = make_upload_use_case(db_session, tmp_path)
    result = await upload.execute(user_id=owner_id, filename="a.png", content=PNG_CONTENT)
    stranger_id = await create_user(db_session)

    with pytest.raises(PhotoNotFoundError):
        await make_delete_use_case(db_session).execute(
            user_id=stranger_id, photo_id=result.photos[0].id
        )


async def test_delete_missing_photo_raises(db_session):
    with pytest.raises(PhotoNotFoundError):
        await make_delete_use_case(db_session).execute(
            user_id="someone", photo_id="no-such-photo"
        )