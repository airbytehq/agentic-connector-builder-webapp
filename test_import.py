#!/usr/bin/env python3
"""Test script to verify app imports and basic functionality."""

try:
    from agentic_connector_builder_webapp.agentic_connector_builder_webapp import app, YamlEditorState
    print("✅ App imported successfully")
    print(f"✅ App object type: {type(app)}")
    print(f"✅ YamlEditorState available: {YamlEditorState}")
    
    # Test state initialization
    state = YamlEditorState()
    print(f"✅ State initialized with content length: {len(state.yaml_content)}")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
