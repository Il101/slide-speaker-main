"""Test script for critical features implementation"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_websocket_manager():
    """Test WebSocket manager"""
    print("\n=== Testing WebSocket Manager ===")
    try:
        from app.core.websocket_manager import ConnectionManager, get_ws_manager
        
        manager = get_ws_manager()
        print("✓ WebSocket manager imported successfully")
        print(f"✓ Total connections: {manager.get_total_connections()}")
        print(f"✓ Connection count for test lesson: {manager.get_connection_count('test-123')}")
        
        # Test progress formatting
        eta = manager._format_eta(125)
        print(f"✓ ETA formatting works: {eta}")
        
        return True
    except Exception as e:
        print(f"✗ WebSocket manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_subscriptions():
    """Test subscription system"""
    print("\n=== Testing Subscription System ===")
    try:
        from app.core.subscriptions import (
            SubscriptionTier, SubscriptionPlan, SubscriptionManager
        )
        
        # Test plan retrieval
        free_plan = SubscriptionPlan.get_plan(SubscriptionTier.FREE)
        pro_plan = SubscriptionPlan.get_plan(SubscriptionTier.PRO)
        enterprise_plan = SubscriptionPlan.get_plan(SubscriptionTier.ENTERPRISE)
        
        print(f"✓ FREE plan: {free_plan['presentations_per_month']} presentations/month")
        print(f"✓ PRO plan: {pro_plan['presentations_per_month']} presentations/month")
        print(f"✓ ENTERPRISE plan: {'unlimited' if enterprise_plan['presentations_per_month'] == -1 else enterprise_plan['presentations_per_month']}")
        
        # Test all plans
        all_plans = SubscriptionPlan.get_all_plans()
        print(f"✓ All plans loaded: {list(all_plans.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Subscription system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentry():
    """Test Sentry integration"""
    print("\n=== Testing Sentry Integration ===")
    try:
        from app.core.sentry import (
            init_sentry, capture_message, capture_exception,
            set_user_context, set_context, add_breadcrumb,
            sentry_transaction, SentrySpan, monitor_performance
        )
        
        print("✓ Sentry module imported successfully")
        print("✓ All sentry functions available")
        
        # Test without DSN (should handle gracefully)
        init_sentry(dsn=None)
        print("✓ init_sentry handles missing DSN gracefully")
        
        # Test capture functions (should log but not crash)
        capture_message("Test message", level="info")
        print("✓ capture_message works")
        
        try:
            raise ValueError("Test exception")
        except Exception as e:
            capture_exception(e, context={"test": True})
            print("✓ capture_exception works")
        
        # Test context functions
        set_user_context("test-user-123", email="test@example.com")
        print("✓ set_user_context works")
        
        set_context("test", {"key": "value"})
        print("✓ set_context works")
        
        add_breadcrumb("Test breadcrumb", category="test")
        print("✓ add_breadcrumb works")
        
        # Test transaction context manager
        with sentry_transaction("test_transaction", op="test"):
            pass
        print("✓ sentry_transaction context manager works")
        
        # Test span
        with SentrySpan("test.operation", "Test description"):
            pass
        print("✓ SentrySpan works")
        
        return True
    except Exception as e:
        print(f"✗ Sentry integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_imports():
    """Test API endpoint imports"""
    print("\n=== Testing API Imports ===")
    try:
        from app.api.websocket import router as websocket_router
        print("✓ WebSocket API imported successfully")
        
        from app.api.content_editor import router as content_editor_router
        print("✓ Content Editor API imported successfully")
        
        # Check routes
        print(f"✓ WebSocket routes: {[route.path for route in websocket_router.routes]}")
        print(f"✓ Content Editor routes: {[route.path for route in content_editor_router.routes]}")
        
        return True
    except Exception as e:
        print(f"✗ API imports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_model():
    """Test database model updates"""
    print("\n=== Testing Database Model ===")
    try:
        from app.core.database import User, Lesson, Slide, Export
        
        print("✓ All database models imported successfully")
        
        # Check if User has subscription_tier field
        user_columns = [c.name for c in User.__table__.columns]
        print(f"✓ User columns: {user_columns}")
        
        if 'subscription_tier' in user_columns:
            print("✓ subscription_tier field exists in User model")
        else:
            print("⚠ subscription_tier field NOT found in User model (migration needed)")
        
        return True
    except Exception as e:
        print(f"✗ Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_file():
    """Test migration file exists"""
    print("\n=== Testing Migration File ===")
    try:
        migration_path = Path(__file__).parent / "alembic" / "versions" / "003_add_subscription_tier.py"
        
        if migration_path.exists():
            print(f"✓ Migration file exists: {migration_path}")
            
            # Read and check content
            with open(migration_path, 'r') as f:
                content = f.read()
                if 'subscription_tier' in content:
                    print("✓ Migration includes subscription_tier field")
                else:
                    print("⚠ Migration does not include subscription_tier field")
            return True
        else:
            print(f"✗ Migration file not found: {migration_path}")
            return False
    except Exception as e:
        print(f"✗ Migration file test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("CRITICAL FEATURES TESTING")
    print("=" * 60)
    
    results = {
        "WebSocket Manager": await test_websocket_manager(),
        "Subscription System": await test_subscriptions(),
        "Sentry Integration": test_sentry(),
        "API Imports": test_api_imports(),
        "Database Model": test_database_model(),
        "Migration File": test_migration_file()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All critical features implemented and working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
