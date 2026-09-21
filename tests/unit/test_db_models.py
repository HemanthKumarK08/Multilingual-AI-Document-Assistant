import pytest
import pytest_asyncio
import uuid
import tempfile
import pathlib
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from app.db.base import Base
from app.db.models import Document, DocumentProcessingJob, User, QueryLogReference
from app.core.security import hash_password, verify_password
from app.core.config import settings

@pytest_asyncio.fixture
async def test_db_session():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_sessionmaker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with test_sessionmaker() as session:
        yield session

    await test_engine.dispose()

@pytest.mark.asyncio
async def test_fresh_db_initialization_and_idempotency():
    """Verify that database initialization on a fresh engine is idempotent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = pathlib.Path(tmpdir) / "test_temp.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")

        # First initialization
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        assert db_file.exists()

        # Second initialization (idempotent run)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await engine.dispose()

@pytest.mark.asyncio
async def test_document_crud(test_db_session: AsyncSession):
    """Test standard document creation and querying."""
    doc = Document(
        doc_id="doc_test_001",
        filename="test_policy.pdf",
        display_title="Test Academic Policy",
        category="academic_regulations",
        language="en",
        file_type="pdf",
        file_size_bytes=1024,
        file_hash_sha256="abc123hash001",
        storage_path="data/raw/academic_regulations/test.pdf",
        page_count=5,
        is_active=True
    )
    test_db_session.add(doc)
    await test_db_session.commit()

    stmt = select(Document).where(Document.doc_id == "doc_test_001")
    result = await test_db_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.display_title == "Test Academic Policy"
    assert retrieved.category == "academic_regulations"
    assert retrieved.is_active is True

@pytest.mark.asyncio
async def test_document_unique_checksum_enforcement(test_db_session: AsyncSession):
    """Test that duplicate SHA-256 hashes are rejected by database unique constraints."""
    doc1 = Document(
        doc_id="doc_test_002",
        filename="test1.pdf",
        display_title="Policy 1",
        category="hostel",
        language="en",
        file_type="pdf",
        file_size_bytes=2048,
        file_hash_sha256="identical_sha256_hash",
        storage_path="data/raw/hostel/test1.pdf",
        is_active=True
    )
    test_db_session.add(doc1)
    await test_db_session.commit()

    doc2 = Document(
        doc_id="doc_test_003",
        filename="test2.pdf",
        display_title="Policy 2",
        category="hostel",
        language="en",
        file_type="pdf",
        file_size_bytes=2048,
        file_hash_sha256="identical_sha256_hash",  # Duplicate hash
        storage_path="data/raw/hostel/test2.pdf",
        is_active=True
    )
    test_db_session.add(doc2)
    with pytest.raises(IntegrityError):
        await test_db_session.commit()
    await test_db_session.rollback()

@pytest.mark.asyncio
async def test_document_soft_deactivation(test_db_session: AsyncSession):
    """Test soft deletion flag toggling without physical record destruction."""
    doc = Document(
        doc_id="doc_test_004",
        filename="soft_delete.pdf",
        display_title="Soft Delete Test",
        category="placements",
        language="en",
        file_type="pdf",
        file_size_bytes=512,
        file_hash_sha256="soft_delete_hash_001",
        storage_path="data/raw/placements/soft.pdf",
        is_active=True
    )
    test_db_session.add(doc)
    await test_db_session.commit()

    # Deactivate
    doc.is_active = False
    await test_db_session.commit()

    # Query active only
    stmt_active = select(Document).where(Document.doc_id == "doc_test_004", Document.is_active == True)
    res_active = await test_db_session.execute(stmt_active)
    assert res_active.scalar_one_or_none() is None

    # Query all
    stmt_all = select(Document).where(Document.doc_id == "doc_test_004")
    res_all = await test_db_session.execute(stmt_all)
    found = res_all.scalar_one()
    assert found.is_active is False

@pytest.mark.asyncio
async def test_foreign_key_enforcement(test_db_session: AsyncSession):
    """Verify that child job records cannot reference non-existent document IDs."""
    orphan_job = DocumentProcessingJob(
        job_id="job_orphan_001",
        doc_id="non_existent_doc_id_999",
        job_type="extraction",
        status="pending"
    )
    test_db_session.add(orphan_job)
    with pytest.raises(IntegrityError):
        await test_db_session.commit()
    await test_db_session.rollback()

@pytest.mark.asyncio
async def test_transaction_rollback(test_db_session: AsyncSession):
    """Verify that uncommitted operations are fully rolled back without state mutation."""
    doc = Document(
        doc_id="doc_rollback_test",
        filename="rollback.pdf",
        display_title="Rollback Test",
        category="scholarships",
        language="en",
        file_type="pdf",
        file_size_bytes=100,
        file_hash_sha256="rollback_hash_001",
        storage_path="data/raw/scholarships/rollback.pdf",
        is_active=True
    )
    test_db_session.add(doc)
    await test_db_session.rollback()

    stmt = select(Document).where(Document.doc_id == "doc_rollback_test")
    result = await test_db_session.execute(stmt)
    assert result.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_user_password_hashing_storage(test_db_session: AsyncSession):
    """Verify that user credentials are saved as PBKDF2 salt:hash and not plaintext."""
    plaintext = "AdminSecretPass123!"
    pw_hash = hash_password(plaintext)
    assert not pw_hash.startswith("AdminSecretPass")
    assert ":" in pw_hash

    user = User(
        user_id="usr_sec_001",
        username="sec_admin",
        role="admin",
        password_hash=pw_hash,
        is_active=True
    )
    test_db_session.add(user)
    await test_db_session.commit()

    stmt = select(User).where(User.username == "sec_admin")
    res = await test_db_session.execute(stmt)
    retrieved = res.scalar_one()
    assert retrieved.password_hash != plaintext
    assert verify_password(plaintext, retrieved.password_hash) is True
    assert verify_password("WrongPassword", retrieved.password_hash) is False

def test_working_directory_independent_db_path():
    """Verify absolute path resolution regardless of invocation CWD."""
    abs_path = settings.absolute_db_path
    assert abs_path.is_absolute()
    assert abs_path.name.endswith(".db")
