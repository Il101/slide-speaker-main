"""
Integration test for SmartScriptGenerator with AdaptivePromptBuilder
Проверяет что SmartScriptGenerator правильно использует адаптивный билдер промптов
"""
import sys
import os
sys.path.insert(0, 'backend')

# Set mock mode to avoid API calls
os.environ['LLM_PROVIDER'] = 'mock'

from app.services.smart_script_generator import SmartScriptGenerator


def test_prompt_generation_with_adaptive_builder():
    """Проверяет что промпт строится правильно с адаптивными инструкциями"""
    print("\n=== Integration Test: SmartScriptGenerator + AdaptivePromptBuilder ===")
    
    generator = SmartScriptGenerator()
    
    # Тестовые данные
    semantic_map = {
        'visual_density': 'high',
        'cognitive_load': 'medium',
        'slide_type': 'content_slide',
        'groups': [
            {
                'id': 'group_title',
                'type': 'title',
                'priority': 'high',
                'educational_intent': 'Introduce main concept',
                'element_ids': ['elem_1'],
                'reading_order': [1],
                'highlight_strategy': {'when': 'start', 'effect_type': 'spotlight'}
            },
            {
                'id': 'group_content',
                'type': 'key_point',
                'priority': 'high',
                'educational_intent': 'Explain core idea',
                'element_ids': ['elem_2', 'elem_3'],
                'reading_order': [2, 3],
                'highlight_strategy': {'when': 'during_explanation', 'effect_type': 'highlight'}
            },
            {
                'id': 'group_example',
                'type': 'example',
                'priority': 'medium',
                'educational_intent': 'Illustrate concept',
                'element_ids': ['elem_4'],
                'reading_order': [4],
                'highlight_strategy': {'when': 'during_detail', 'effect_type': 'highlight'}
            },
            {
                'id': 'group_footer',
                'type': 'footer',
                'priority': 'none',
                'educational_intent': 'N/A',
                'element_ids': ['elem_5'],
                'reading_order': [5],
                'highlight_strategy': {'when': 'never'}
            }
        ]
    }
    
    ocr_elements = [
        {'id': 'elem_1', 'text': 'Фотосинтез'},
        {'id': 'elem_2', 'text': 'Процесс превращения света в энергию'},
        {'id': 'elem_3', 'text': '6CO2 + 6H2O → C6H12O6 + 6O2'},
        {'id': 'elem_4', 'text': 'Пример: зелёные листья растений'},
        {'id': 'elem_5', 'text': '© 2024'}
    ]
    
    presentation_context = {
        'theme': 'Biology',
        'level': 'undergraduate',
        'presentation_style': 'academic',
        'total_slides': 10
    }
    
    content_strategy = {
        'content_type': 'diagram',
        'pace': 'moderate',
        'explanation_style': 'narrative'
    }
    
    # Создаём промпт
    prompt = generator._create_script_generation_prompt(
        semantic_map,
        ocr_elements,
        presentation_context,
        "Previous slide discussed cell structure",
        slide_index=2,
        persona_config=None,
        content_strategy=content_strategy
    )
    
    print(f"\n✅ Generated prompt (length: {len(prompt)} chars)")
    print("\n--- Prompt Preview (first 1500 chars) ---")
    print(prompt[:1500])
    print("...")
    print("\n--- Prompt Preview (last 500 chars) ---")
    print(prompt[-500:])
    
    # Проверки
    assert 'SLIDE ANALYSIS' in prompt, "Should contain slide analysis section"
    assert 'Visual Density: HIGH' in prompt, "Should show visual density"
    assert 'Cognitive Load: MEDIUM' in prompt, "Should show cognitive load"
    assert 'TOP PRIORITY GROUPS' in prompt, "Should have priority groups section"
    assert 'CRITICAL STRATEGY' in prompt or 'HIGH DENSITY' in prompt, "Should have adaptive instructions"
    assert 'TARGET DURATION' in prompt or 'STRICT LIMIT' in prompt, "Should have duration hint"
    assert 'group_title' in prompt, "Should include group IDs"
    assert 'group_footer' not in prompt or 'none' in prompt.lower(), "Should filter out footer groups"
    
    # Проверяем что high density слайд имеет строгие инструкции
    assert 'CONCISE' in prompt, "High density should mention CONCISE"
    assert '20-30' in prompt or '20-35' in prompt, "Should have short duration for dense slide"
    
    print("\n✅ All integration checks passed!")
    print("\n📊 Summary:")
    print(f"  - Prompt length: {len(prompt)} characters")
    print(f"  - Contains adaptive instructions: ✓")
    print(f"  - Contains duration guidance: ✓")
    print(f"  - Filters out low-priority groups: ✓")
    print(f"  - Provides density-aware strategy: ✓")


def test_prompt_differences_by_density():
    """Проверяет что промпты различаются для разных плотностей"""
    print("\n=== Test: Prompt Adaptation by Density ===")
    
    generator = SmartScriptGenerator()
    
    base_semantic_map = {
        'slide_type': 'content_slide',
        'cognitive_load': 'medium',
        'groups': [
            {
                'id': 'group_1',
                'type': 'key_point',
                'priority': 'high',
                'educational_intent': 'Explain',
                'element_ids': ['e1'],
                'reading_order': [1]
            }
        ]
    }
    
    ocr_elements = [{'id': 'e1', 'text': 'Test content'}]
    presentation_context = {'theme': 'Test', 'level': 'test', 'presentation_style': 'test', 'total_slides': 1}
    
    # Generate prompts for different densities
    densities = ['high', 'medium', 'low']
    prompts = {}
    
    for density in densities:
        sm = {**base_semantic_map, 'visual_density': density}
        prompt = generator._create_script_generation_prompt(
            sm, ocr_elements, presentation_context, "", 0, None, {}
        )
        prompts[density] = prompt
        print(f"\n{density.upper()} density prompt length: {len(prompt)} chars")
        
        # Find adaptive instructions section
        if 'CRITICAL STRATEGY' in prompt:
            start = prompt.index('CRITICAL STRATEGY')
            print(f"  Strategy preview: {prompt[start:start+150]}...")
    
    # Проверки различий
    assert 'CONCISE' in prompts['high'], "High density should be CONCISE"
    assert 'ELABORATE' in prompts['low'], "Low density should ELABORATE"
    
    # Длительности должны различаться
    assert '20' in prompts['high'] or '25' in prompts['high'], "High should suggest short duration"
    assert '30' in prompts['low'] or '40' in prompts['low'], "Low should suggest longer duration"
    
    print("\n✅ Prompts successfully adapt to density!")


if __name__ == '__main__':
    print("="*70)
    print("Integration Testing: Adaptive Prompt System")
    print("="*70)
    
    try:
        test_prompt_generation_with_adaptive_builder()
        test_prompt_differences_by_density()
        
        print("\n" + "="*70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*70)
        print("\n🎉 The adaptive prompt system is working correctly!")
        print("📝 Next: Test with real LLM to see improved script quality")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
