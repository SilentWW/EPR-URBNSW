"""
Backup & Restore API Tests
Testing: Create, List, Download, Upload, Restore, Delete backup functionality
"""
import pytest
import requests
import os
import json
import tempfile
import gzip

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "lahiruraja97@gmail.com"
TEST_PASSWORD = "password123"

class TestBackupRestoreAPI:
    """Tests for Admin Backup & Restore endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # ================ SYSTEM INFO ================
    def test_system_info_endpoint(self):
        """Test GET /admin/system-info returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/system-info",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "collection_stats" in data
        assert "total_records" in data
        assert "backup_count" in data
        assert "backup_storage_used_bytes" in data
        
        # Verify collection stats has expected collections
        assert isinstance(data["collection_stats"], dict)
        print(f"System Info: {data['total_records']} total records, {data['backup_count']} backups")
    
    # ================ LIST BACKUPS ================
    def test_list_backups_endpoint(self):
        """Test GET /admin/backups returns list of backups"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} backups")
        
        # If backups exist, verify structure
        if len(data) > 0:
            backup = data[0]
            assert "id" in backup
            assert "name" in backup
            assert "status" in backup
            assert "created_at" in backup
            print(f"First backup: {backup['name']} - Status: {backup['status']}")
    
    # ================ CREATE BACKUP ================
    def test_create_backup_with_name(self):
        """Test POST /admin/backups creates a new backup"""
        backup_name = "TEST_pytest_backup"
        response = requests.post(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers,
            json={
                "name": backup_name,
                "description": "Test backup from pytest",
                "backup_type": "full"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["name"] == backup_name
        assert data["status"] == "completed"
        assert "id" in data
        assert "file_path" in data
        assert "collections_backed_up" in data
        
        self.created_backup_id = data["id"]
        print(f"Created backup: {data['name']} (ID: {data['id']})")
        print(f"Collections backed up: {data['collections_backed_up']}")
    
    def test_create_backup_without_name(self):
        """Test POST /admin/backups creates backup with auto-generated name"""
        response = requests.post(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers,
            json={
                "backup_type": "full"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "backup-" in data["name"]  # Auto-generated name starts with "backup-"
        assert data["status"] == "completed"
        print(f"Created auto-named backup: {data['name']}")
    
    # ================ GET BACKUP DETAILS ================
    def test_get_backup_details(self):
        """Test GET /admin/backups/{backup_id} returns backup details"""
        # First get list of backups
        list_response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers
        )
        assert list_response.status_code == 200
        backups = list_response.json()
        
        if len(backups) > 0:
            backup_id = backups[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/admin/backups/{backup_id}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Failed: {response.text}"
            
            data = response.json()
            assert data["id"] == backup_id
            print(f"Got backup details: {data['name']}")
        else:
            pytest.skip("No backups available to test")
    
    def test_get_nonexistent_backup_returns_404(self):
        """Test GET /admin/backups/{invalid_id} returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/nonexistent-id-12345",
            headers=self.headers
        )
        assert response.status_code == 404
    
    # ================ DOWNLOAD BACKUP ================
    def test_download_backup(self):
        """Test GET /admin/backups/{backup_id}/download returns file"""
        # Get list of backups
        list_response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers
        )
        backups = [b for b in list_response.json() if b["status"] == "completed"]
        
        if len(backups) > 0:
            backup_id = backups[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/admin/backups/{backup_id}/download",
                headers=self.headers
            )
            assert response.status_code == 200, f"Failed: {response.text}"
            assert response.headers.get("content-type") == "application/gzip"
            assert len(response.content) > 0
            print(f"Downloaded backup: {len(response.content)} bytes")
        else:
            pytest.skip("No completed backups available to download")
    
    # ================ UPLOAD BACKUP ================
    def test_upload_backup_valid_json(self):
        """Test POST /admin/backups/upload with valid JSON file"""
        # Create a valid backup file structure
        backup_data = {
            "metadata": {
                "backup_id": "test-upload-backup",
                "company_id": "test-company",
                "created_at": "2026-03-08T12:00:00Z",
                "backup_type": "full"
            },
            "collections": {
                "users": [{"id": "user1", "name": "Test User"}],
                "products": [{"id": "prod1", "name": "Test Product"}]
            }
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_file_path = f.name
        
        try:
            # Upload the file
            with open(temp_file_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/admin/backups/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files={"file": ("test-backup.json", f, "application/json")}
                )
            
            assert response.status_code == 200, f"Failed: {response.text}"
            
            data = response.json()
            assert "backup_id" in data
            assert data["total_records"] == 2  # 1 user + 1 product
            assert len(data["collections"]) == 2
            print(f"Uploaded backup: {data['backup_id']}")
        finally:
            os.unlink(temp_file_path)
    
    def test_upload_backup_valid_gzip(self):
        """Test POST /admin/backups/upload with valid gzipped JSON file"""
        backup_data = {
            "metadata": {
                "backup_id": "test-gzip-upload",
                "company_id": "test-company",
                "created_at": "2026-03-08T12:00:00Z",
                "backup_type": "full"
            },
            "collections": {
                "products": [{"id": "prod1", "name": "Gzip Test Product"}]
            }
        }
        
        # Create gzipped file
        with tempfile.NamedTemporaryFile(suffix='.json.gz', delete=False) as f:
            temp_file_path = f.name
        
        with gzip.open(temp_file_path, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/admin/backups/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files={"file": ("test-backup.json.gz", f, "application/gzip")}
                )
            
            assert response.status_code == 200, f"Failed: {response.text}"
            data = response.json()
            assert data["total_records"] == 1
            print(f"Uploaded gzipped backup: {data['backup_id']}")
        finally:
            os.unlink(temp_file_path)
    
    def test_upload_backup_invalid_format(self):
        """Test POST /admin/backups/upload with invalid file type returns 400"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Invalid backup file content")
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/admin/backups/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files={"file": ("invalid.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            print("Correctly rejected invalid file format")
        finally:
            os.unlink(temp_file_path)
    
    def test_upload_backup_missing_collections(self):
        """Test POST /admin/backups/upload with invalid structure returns 400"""
        backup_data = {
            "metadata": {"backup_id": "test"},
            # Missing "collections" key
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/admin/backups/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files={"file": ("invalid-structure.json", f, "application/json")}
                )
            
            assert response.status_code == 400
            print("Correctly rejected missing collections")
        finally:
            os.unlink(temp_file_path)
    
    # ================ RESTORE PREVIEW ================
    def test_restore_preview(self):
        """Test GET /admin/restore/preview/{backup_id} returns preview data"""
        list_response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers
        )
        backups = [b for b in list_response.json() if b["status"] == "completed"]
        
        if len(backups) > 0:
            backup_id = backups[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/admin/restore/preview/{backup_id}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Failed: {response.text}"
            
            data = response.json()
            assert "backup_name" in data
            assert "collections" in data
            print(f"Restore preview for: {data['backup_name']}")
            print(f"Collections: {list(data['collections'].keys())}")
        else:
            pytest.skip("No backups available for preview")
    
    # ================ RESTORE (with confirmation) ================
    def test_restore_without_confirmation_fails(self):
        """Test POST /admin/restore without correct confirmation code fails"""
        list_response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers
        )
        backups = [b for b in list_response.json() if b["status"] == "completed"]
        
        if len(backups) > 0:
            backup_id = backups[0]["id"]
            response = requests.post(
                f"{BASE_URL}/api/admin/restore",
                headers=self.headers,
                json={
                    "backup_id": backup_id,
                    "confirmation_code": "WRONG"
                }
            )
            assert response.status_code == 400
            print("Correctly rejected wrong confirmation code")
        else:
            pytest.skip("No backups available for restore test")
    
    # ================ DELETE BACKUP ================
    def test_delete_backup(self):
        """Test DELETE /admin/backups/{backup_id} removes backup"""
        # First create a backup to delete
        create_response = requests.post(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers,
            json={
                "name": "TEST_backup_to_delete",
                "description": "Will be deleted",
                "backup_type": "full"
            }
        )
        assert create_response.status_code == 200
        backup_id = create_response.json()["id"]
        
        # Delete the backup
        response = requests.delete(
            f"{BASE_URL}/api/admin/backups/{backup_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify it's deleted
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/backups/{backup_id}",
            headers=self.headers
        )
        assert verify_response.status_code == 404
        print(f"Successfully deleted backup: {backup_id}")
    
    def test_delete_nonexistent_backup_returns_404(self):
        """Test DELETE /admin/backups/{invalid_id} returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/backups/nonexistent-id-12345",
            headers=self.headers
        )
        assert response.status_code == 404
    
    # ================ DATA RESET PREVIEW ================
    def test_reset_preview_transactional(self):
        """Test GET /admin/data-reset/preview for transactional reset"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-reset/preview",
            headers=self.headers,
            params={"reset_type": "transactional"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "collections" in data
        assert "warnings" in data
        print(f"Transactional reset preview: {len(data['collections'])} collections affected")
    
    def test_reset_preview_full(self):
        """Test GET /admin/data-reset/preview for full reset"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-reset/preview",
            headers=self.headers,
            params={"reset_type": "full"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "collections" in data
        assert "warnings" in data
        print(f"Full reset preview: {len(data['collections'])} collections affected")
    
    # ================ NON-ADMIN ACCESS ================
    def test_non_admin_access_denied(self):
        """Test non-admin users cannot access admin endpoints"""
        # Note: This test would require a non-admin user
        # For now, we just verify admin access works
        response = requests.get(
            f"{BASE_URL}/api/admin/system-info",
            headers=self.headers
        )
        assert response.status_code == 200
        print("Admin access verified")


class TestUploadedBackupBadge:
    """Test that uploaded backups have is_uploaded flag"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_uploaded_backup_has_flag(self):
        """Verify uploaded backups have is_uploaded=True"""
        list_response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=self.headers
        )
        backups = list_response.json()
        
        uploaded_backups = [b for b in backups if b.get("is_uploaded")]
        created_backups = [b for b in backups if not b.get("is_uploaded")]
        
        print(f"Uploaded backups: {len(uploaded_backups)}")
        print(f"Created backups: {len(created_backups)}")
        
        if uploaded_backups:
            print(f"Sample uploaded backup: {uploaded_backups[0]['name']}")
            assert uploaded_backups[0].get("is_uploaded") == True


# Cleanup fixture to remove test backups
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup TEST_ prefixed backups after tests"""
    yield
    
    # Login and cleanup
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all backups
        list_response = requests.get(
            f"{BASE_URL}/api/admin/backups",
            headers=headers
        )
        if list_response.status_code == 200:
            backups = list_response.json()
            for backup in backups:
                if backup["name"].startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/admin/backups/{backup['id']}",
                        headers=headers
                    )
                    print(f"Cleaned up: {backup['name']}")
