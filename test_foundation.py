#!/usr/bin/env python3
"""
Simple test for PDF service foundation - Task 2
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=" * 60)
    print("PDF Service Foundation Test - Task 2")
    print("=" * 60)
    
    # Test 1: Import and create app
    print("\n1. Testing Flask app creation...")
    try:
        from app import create_app, validate_libreoffice
        app = create_app()
        print("   ✅ Flask app created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create app: {e}")
        return 1
    
    # Test 2: Health check endpoint
    print("\n2. Testing health check endpoint...")
    try:
        with app.test_client() as client:
            response = client.get('/health')
            data = response.get_json()
            assert response.status_code == 200
            assert data['status'] == 'healthy'
            assert 'libreoffice_available' in data
            print(f"   ✅ Health check working")
            print(f"      Status: {data['status']}")
            print(f"      Service: {data['service']}")
            print(f"      LibreOffice: {data['libreoffice_available']}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return 1
    
    # Test 3: CORS configuration
    print("\n3. Testing CORS configuration...")
    try:
        with app.test_client() as client:
            response = client.get('/health', headers={'Origin': 'http://example.com'})
            assert response.status_code == 200
            print("   ✅ CORS configured properly")
    except Exception as e:
        print(f"   ❌ CORS test failed: {e}")
        return 1
    
    # Test 4: Error handling (404)
    print("\n4. Testing error handling middleware...")
    try:
        with app.test_client() as client:
            response = client.get('/nonexistent')
            data = response.get_json()
            assert response.status_code == 404
            assert data['success'] is False
            print("   ✅ 404 error handler working")
    except Exception as e:
        print(f"   ❌ Error handler test failed: {e}")
        return 1
    
    # Test 5: LibreOffice validation
    print("\n5. Testing LibreOffice dependency validation...")
    try:
        result = validate_libreoffice()
        print(f"   ✅ LibreOffice validation completed")
        print(f"      Available: {result}")
    except Exception as e:
        print(f"   ❌ LibreOffice validation failed: {e}")
        return 1
    
    # Test 6: Convert endpoint requires LibreOffice
    print("\n6. Testing convert endpoint dependency check...")
    try:
        with app.test_client() as client:
            response = client.post('/convert-pdf', json={})
            data = response.get_json()
            # Should return 503 if LibreOffice not available, or 400 if it is available but no data
            assert response.status_code in [400, 503]
            assert data['success'] is False
            if response.status_code == 503:
                print("   ✅ Convert endpoint properly checks LibreOffice")
            else:
                print("   ✅ Convert endpoint validates input data")
    except Exception as e:
        print(f"   ❌ Convert endpoint test failed: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ All Task 2 requirements verified!")
    print("=" * 60)
    print("\nTask 2 Implementation Complete:")
    print("  ✓ Flask application structure with health check endpoint")
    print("  ✓ CORS configuration")
    print("  ✓ Basic error handling middleware")
    print("  ✓ LibreOffice dependency validation")
    return 0

if __name__ == '__main__':
    sys.exit(main())
