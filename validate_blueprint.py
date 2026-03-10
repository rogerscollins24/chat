#!/usr/bin/env python3
"""Validate render.yaml against Render Blueprint specifications"""

import yaml
import sys

def validate_blueprint():
    """Validate the render.yaml file"""
    
    try:
        with open('render.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("=" * 70)
        print("RENDER BLUEPRINT VALIDATION REPORT")
        print("=" * 70)
        
        errors = []
        warnings = []
        
        # Check root structure
        if 'services' not in config:
            errors.append("Missing 'services' key at root level")
            print(f"\n❌ ERRORS (1):")
            print(f"  • {errors[0]}")
            return 1
        
        services = config.get('services', [])
        if not isinstance(services, list):
            errors.append("'services' must be a list")
            print(f"\n❌ ERRORS (1):")
            print(f"  • {errors[0]}")
            return 1
        
        print(f"\n✅ Found {len(services)} service(s)")
        
        # Validate each service
        for i, service in enumerate(services):
            print(f"\n{'─' * 70}")
            print(f"Service {i+1}: {service.get('name', 'UNNAMED')}")
            print(f"{'─' * 70}")
            
            # Required fields
            required = ['type', 'name', 'runtime']
            for field in required:
                if field not in service:
                    errors.append(f"Service '{service.get('name')}': Missing required field '{field}'")
                else:
                    print(f"  ✓ {field}: {service[field]}")
            
            # Validate runtime
            runtime = service.get('runtime', '').lower()
            valid_runtimes = ['python', 'node', 'ruby', 'go', 'deno', 'docker']
            if runtime and runtime not in valid_runtimes:
                errors.append(f"Service '{service.get('name')}': Invalid runtime '{runtime}'. Valid: {', '.join(valid_runtimes)}")
            
            # Validate plan
            plan = service.get('plan', '')
            valid_plans = ['free', 'starter', 'standard']
            if plan and plan not in valid_plans:
                errors.append(f"Service '{service.get('name')}': Invalid plan '{plan}'. Valid: {', '.join(valid_plans)}")
            else:
                print(f"  ✓ plan: {plan}")
            
            # Validate build/start commands
            if 'buildCommand' in service:
                print(f"  ✓ buildCommand: {service['buildCommand'][:50]}...")
            
            if 'startCommand' in service:
                print(f"  ✓ startCommand: {service['startCommand'][:50]}...")
            
            # Validate environment variables
            env_vars = service.get('envVars', [])
            if env_vars:
                print(f"\n  Environment Variables ({len(env_vars)}):")
                for env in env_vars:
                    if 'key' not in env:
                        errors.append(f"Service '{service.get('name')}': envVar missing 'key'")
                    elif 'value' not in env and 'fromService' not in env:
                        errors.append(f"Service '{service.get('name')}': envVar '{env['key']}' missing 'value' or 'fromService'")
                    else:
                        val = env.get('value', "[from service]")
                        if len(str(val)) > 50:
                            val = str(val)[:50] + "..."
                        print(f"    • {env['key']}: {val}")
                        
                        # Check for common issues
                        if env['key'] == 'DATABASE_URL' and 'localhost' in str(env.get('value', '')):
                            warnings.append(f"Service '{service.get('name')}': DATABASE_URL points to localhost - won't work in production")
                        
                        if env['key'] == 'CORS_ORIGINS' and 'localhost' in str(env.get('value', '')):
                            warnings.append(f"Service '{service.get('name')}': CORS_ORIGINS contains localhost - consider using environment-specific values")
        
        # Summary
        print(f"\n{'=' * 70}")
        print("VALIDATION SUMMARY")
        print(f"{'=' * 70}")
        print(f"Services: {len(services)}")
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        
        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("\n✅ Blueprint is valid!")
            return 0
        elif not errors:
            print("\n✅ Blueprint is valid (with warnings)")
            return 0
        else:
            print("\n❌ Blueprint has errors - please fix before deploying")
            return 1
            
    except FileNotFoundError:
        print("❌ Error: render.yaml not found")
        return 1
    except yaml.YAMLError as e:
        print(f"❌ Error: Invalid YAML: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit_code = validate_blueprint()
    sys.exit(exit_code)
