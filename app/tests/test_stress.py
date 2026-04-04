import time
import pytest
from app.models.task import TaskStatus, TaskPriority


class TestStressLoad:
    """Stress test with 1000+ record simulation."""

    def test_bulk_task_creation(self, client, admin_user, admin_headers):
        """Create 1000+ tasks and verify listing performance."""
        priorities = ["low", "medium", "high"]
        owner_id = admin_user["id"]

        # Create 1000 tasks
        for i in range(1000):
            response = client.post("/tasks/", json={
                "title": f"Stress Task {i}",
                "description": f"Description for task {i}",
                "priority": priorities[i % 3],
                "owner_id": owner_id,
            }, headers=admin_headers)
            assert response.status_code == 201, f"Failed creating task {i}: {response.text}"

        # Verify count via listing
        start = time.time()
        response = client.get("/tasks/?limit=10000", headers=admin_headers)
        list_duration = time.time() - start
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1000
        print(f"\nList 1000 tasks: {list_duration:.3f}s")

    def test_bulk_task_filtering(self, client, admin_user, admin_headers):
        """Create tasks and test filtered queries performance."""
        owner_id = admin_user["id"]
        for i in range(500):
            client.post("/tasks/", json={
                "title": f"Filter Task {i}",
                "description": f"Desc {i}",
                "priority": "high" if i % 2 == 0 else "low",
                "owner_id": owner_id,
            }, headers=admin_headers)

        start = time.time()
        response = client.get("/tasks/?priority=high&limit=10000", headers=admin_headers)
        filter_duration = time.time() - start
        assert response.status_code == 200
        high_tasks = response.json()
        assert len(high_tasks) == 250
        print(f"\nFilter 250 high-priority from 500: {filter_duration:.3f}s")

    def test_bulk_user_creation(self, client, admin_user, admin_headers):
        """Create 100 users and verify listing."""
        for i in range(100):
            response = client.post("/users/", json={
                "email": f"stress{i}@test.com",
                "password": "password123",
                "full_name": f"Stress User {i}",
            }, headers=admin_headers)
            assert response.status_code == 201, f"Failed creating user {i}: {response.text}"

        start = time.time()
        response = client.get("/users/?limit=200", headers=admin_headers)
        list_duration = time.time() - start
        assert response.status_code == 200
        users = response.json()
        # 100 stress users + 1 admin
        assert len(users) >= 101
        print(f"\nList 100+ users: {list_duration:.3f}s")

    def test_dashboard_with_large_dataset(self, client, admin_user, admin_headers):
        """Test dashboard analytics with 500+ tasks."""
        owner_id = admin_user["id"]
        for i in range(500):
            client.post("/tasks/", json={
                "title": f"Dashboard Task {i}",
                "description": f"Desc {i}",
                "priority": ["low", "medium", "high"][i % 3],
                "owner_id": owner_id,
            }, headers=admin_headers)

        start = time.time()
        response = client.get("/dashboard/summary", headers=admin_headers)
        summary_duration = time.time() - start
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 500
        print(f"\nDashboard summary (500 tasks): {summary_duration:.3f}s")

        start = time.time()
        response = client.get("/dashboard/by-priority", headers=admin_headers)
        priority_duration = time.time() - start
        assert response.status_code == 200
        print(f"Dashboard by-priority (500 tasks): {priority_duration:.3f}s")

        start = time.time()
        response = client.get("/dashboard/completion-rate", headers=admin_headers)
        rate_duration = time.time() - start
        assert response.status_code == 200
        print(f"Dashboard completion-rate (500 tasks): {rate_duration:.3f}s")
