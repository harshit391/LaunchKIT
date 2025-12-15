#!/usr/bin/env python3
"""
LaunchKIT Installation Test Script
Tests if all dependencies and modules are properly installed
"""
import sys
import platform


def test_python_version():
    """Test Python version"""
    print("=" * 60)
    print("🐍 Testing Python Version...")
    print("=" * 60)

    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    print(f"Python Path: {sys.executable}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False

    print("✅ Python version is compatible")
    return True


def test_platform_detection():
    """Test platform detection"""
    print("\n" + "=" * 60)
    print("💻 Testing Platform Detection...")
    print("=" * 60)

    print(f"System: {platform.system()}")
    print(f"Release: {platform.release()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")

    return True


def test_dependencies():
    """Test required dependencies"""
    print("\n" + "=" * 60)
    print("📦 Testing Dependencies...")
    print("=" * 60)

    required_packages = {
        "questionary": "Interactive CLI prompts",
        "names": "Random name generation",
        "pygithub": "GitHub API integration",
        "docker": "Docker integration",
        "jinja2": "Template rendering",
        "pytest": "Testing framework",
        "rich": "Terminal formatting",
        "yaml": "YAML parsing (pyyaml)",
    }

    all_installed = True

    for package, description in required_packages.items():
        try:
            if package == "yaml":
                __import__("yaml")
            else:
                __import__(package)
            print(f"✅ {package:15} - {description}")
        except ImportError:
            print(f"❌ {package:15} - {description} (NOT INSTALLED)")
            all_installed = False

    return all_installed


def test_launchkit_imports():
    """Test LaunchKIT module imports"""
    print("\n" + "=" * 60)
    print("🚀 Testing LaunchKIT Modules...")
    print("=" * 60)

    modules_to_test = [
        ("launchkit", "Main package"),
        ("launchkit.cli", "CLI module"),
        ("launchkit.utils.platform_utils", "Platform utilities"),
        ("launchkit.utils.security_utils", "Security utilities"),
        ("launchkit.utils.learning_mode", "Learning mode"),
        ("launchkit.utils.display_utils", "Display utilities"),
        ("launchkit.core.git_tools", "Git tools"),
        ("launchkit.modules.project_management", "Project management"),
    ]

    all_imported = True

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name:40} - {description}")
        except ImportError as e:
            print(f"❌ {module_name:40} - {description}")
            print(f"   Error: {e}")
            all_imported = False

    return all_imported


def test_platform_utils():
    """Test platform utilities"""
    print("\n" + "=" * 60)
    print("🔧 Testing Platform Utilities...")
    print("=" * 60)

    try:
        from launchkit.utils.platform_utils import (
            PlatformDetector,
            VirtualEnvUtils,
            CommandUtils,
            PathUtils
        )

        # Test platform detection
        is_windows = PlatformDetector.is_windows()
        is_macos = PlatformDetector.is_macos()
        is_linux = PlatformDetector.is_linux()
        platform_name = PlatformDetector.get_platform_name()

        print(f"Platform: {platform_name}")
        print(f"  - Windows: {is_windows}")
        print(f"  - macOS: {is_macos}")
        print(f"  - Linux: {is_linux}")

        # Test path utilities
        home_dir = PathUtils.get_home_dir()
        print(f"Home Directory: {home_dir}")

        # Test command utilities
        shell = CommandUtils.get_shell_command()
        print(f"Shell Command: {shell}")

        print("✅ Platform utilities working correctly")
        return True

    except Exception as e:
        print(f"❌ Platform utilities error: {e}")
        return False


def test_security_utils():
    """Test security utilities"""
    print("\n" + "=" * 60)
    print("🔒 Testing Security Utilities...")
    print("=" * 60)

    try:
        from launchkit.utils.security_utils import SecurityValidator, CommandBuilder

        # Test project name validation
        try:
            SecurityValidator.validate_project_name("test-project-123")
            print("✅ Project name validation works")
        except Exception as e:
            print(f"❌ Project name validation failed: {e}")
            return False

        # Test command builder
        git_cmd = CommandBuilder.build_git_command("init")
        print(f"✅ Command builder works: {git_cmd}")

        # Test secret generation
        secret = SecurityValidator.generate_secret_key()
        print(f"✅ Secret generation works (length: {len(secret)})")

        return True

    except Exception as e:
        print(f"❌ Security utilities error: {e}")
        return False


def test_learning_mode():
    """Test learning mode"""
    print("\n" + "=" * 60)
    print("📚 Testing Learning Mode...")
    print("=" * 60)

    try:
        from launchkit.utils.learning_mode import LearningMode, CommandExplainer

        # Test command explanation
        explanation = CommandExplainer.explain_command(["git", "init"])
        if explanation.get("base_command") == "git":
            print("✅ Command explanation works")
        else:
            print("❌ Command explanation failed")
            return False

        # Test learning mode state
        print(f"Learning Mode Enabled: {LearningMode.is_enabled()}")
        print("✅ Learning mode module works")

        return True

    except Exception as e:
        print(f"❌ Learning mode error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " LaunchKIT Installation Test ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    tests = [
        ("Python Version", test_python_version),
        ("Platform Detection", test_platform_detection),
        ("Dependencies", test_dependencies),
        ("LaunchKIT Imports", test_launchkit_imports),
        ("Platform Utilities", test_platform_utils),
        ("Security Utilities", test_security_utils),
        ("Learning Mode", test_learning_mode),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! LaunchKIT is properly installed.")
        print("\nYou can now run LaunchKIT with:")
        print("  python main.py")
        print("or:")
        print("  launchkit")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        print("\nCommon fixes:")
        print("  1. Install missing dependencies:")
        print("     pip install -r requirements.txt")
        print("  2. Ensure you're in the LaunchKIT directory")
        print("  3. Check Python version (3.8+ required)")
        print("  4. Try reinstalling:")
        print("     pip install -r requirements.txt --force-reinstall")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
