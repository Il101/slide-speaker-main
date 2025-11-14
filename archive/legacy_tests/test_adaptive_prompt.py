"""
Test script for AdaptivePromptBuilder
Проверяет работу адаптивной системы генерации промптов
"""
import sys
sys.path.insert(0, 'backend')

from app.services.adaptive_prompt_builder import AdaptivePromptBuilder


def test_high_density_slide():
    """Тест плотного слайда с множеством информации"""
    print("\n=== TEST 1: High Density Slide ===")
    
    builder = AdaptivePromptBuilder()
    
    # Симуляция плотного слайда с множеством групп
    semantic_map = {
        'visual_density': 'high',
        'cognitive_load': 'medium',
        'slide_type': 'content_slide',
        'groups': [
            {
                'id': 'group_title',
                'type': 'title',
                'priority': 'high',
                'educational_intent': 'Introduce main topic',
                'element_ids': ['elem_1', 'elem_2'],
                'reading_order': [1, 2]
            },
            {
                'id': 'group_formula',
                'type': 'key_point',
                'priority': 'high',
                'educational_intent': 'Explain formula',
                'element_ids': ['elem_3'],
                'reading_order': [3]
            },
            {
                'id': 'group_example1',
                'type': 'example',
                'priority': 'medium',
                'educational_intent': 'Show example',
                'element_ids': ['elem_4'],
                'reading_order': [4]
            },
            {
                'id': 'group_example2',
                'type': 'example',
                'priority': 'low',
                'educational_intent': 'Additional example',
                'element_ids': ['elem_5'],
                'reading_order': [5]
            },
            {
                'id': 'group_footer',
                'type': 'footer',
                'priority': 'none',
                'educational_intent': 'N/A',
                'element_ids': ['elem_6'],
                'reading_order': [6]
            }
        ]
    }
    
    ocr_elements = [
        {'id': 'elem_1', 'text': 'Анатомическое строение листа'},
        {'id': 'elem_2', 'text': 'Основные типы'},
        {'id': 'elem_3', 'text': 'Epidermis + Mesophyll + Vascular'},
        {'id': 'elem_4', 'text': 'Пример: дубовый лист'},
        {'id': 'elem_5', 'text': 'Пример: берёзовый лист'},
        {'id': 'elem_6', 'text': '© 2024'}
    ]
    
    groups_text, filtered_groups, optimal_duration = builder.build_adaptive_groups_section(
        semantic_map, ocr_elements
    )
    
    print(f"Filtered groups: {len(filtered_groups)} (из {len(semantic_map['groups'])} total)")
    print(f"Optimal duration: {optimal_duration}s")
    print(f"\nGroups section:\n{groups_text}")
    
    adaptive_instructions = builder.generate_adaptive_instructions(
        semantic_map,
        {'content_type': 'diagram'},
        len(filtered_groups)
    )
    print(f"\nAdaptive instructions:\n{adaptive_instructions}")
    
    duration_hint = builder.build_duration_hint(optimal_duration, 'high')
    print(f"\nDuration hint:\n{duration_hint}")
    
    # Проверки
    assert len(filtered_groups) <= 4, f"High density should filter to ≤4 groups, got {len(filtered_groups)}"
    assert optimal_duration < 40, f"High density should have short duration, got {optimal_duration}s"
    assert 'CONCISE' in adaptive_instructions, "Should mention CONCISE for high density"
    print("\n✅ Test 1 PASSED")


def test_low_density_slide():
    """Тест простого слайда с малым количеством информации"""
    print("\n=== TEST 2: Low Density Slide ===")
    
    builder = AdaptivePromptBuilder()
    
    semantic_map = {
        'visual_density': 'low',
        'cognitive_load': 'easy',
        'slide_type': 'title_slide',
        'groups': [
            {
                'id': 'group_title',
                'type': 'title',
                'priority': 'high',
                'educational_intent': 'Introduce topic',
                'element_ids': ['elem_1'],
                'reading_order': [1]
            },
            {
                'id': 'group_subtitle',
                'type': 'heading',
                'priority': 'medium',
                'educational_intent': 'Context',
                'element_ids': ['elem_2'],
                'reading_order': [2]
            }
        ]
    }
    
    ocr_elements = [
        {'id': 'elem_1', 'text': 'Введение в биологию'},
        {'id': 'elem_2', 'text': 'Лекция 1'}
    ]
    
    groups_text, filtered_groups, optimal_duration = builder.build_adaptive_groups_section(
        semantic_map, ocr_elements
    )
    
    print(f"Filtered groups: {len(filtered_groups)}")
    print(f"Optimal duration: {optimal_duration}s")
    
    adaptive_instructions = builder.generate_adaptive_instructions(
        semantic_map,
        {'content_type': 'text'},
        len(filtered_groups)
    )
    
    # Проверки
    assert len(filtered_groups) == 2, f"All groups should pass filter, got {len(filtered_groups)}"
    assert optimal_duration >= 30, f"Low density should have min 30s duration, got {optimal_duration}s"
    assert 'ELABORATE' in adaptive_instructions, "Should mention ELABORATE for low density"
    print("✅ Test 2 PASSED")


def test_complex_cognitive_load():
    """Тест сложного контента"""
    print("\n=== TEST 3: Complex Cognitive Load ===")
    
    builder = AdaptivePromptBuilder()
    
    semantic_map = {
        'visual_density': 'medium',
        'cognitive_load': 'complex',
        'slide_type': 'content_slide',
        'groups': [
            {
                'id': 'group_formula',
                'type': 'key_point',
                'priority': 'high',
                'educational_intent': 'Explain complex formula',
                'element_ids': ['elem_1'],
                'reading_order': [1]
            }
        ]
    }
    
    ocr_elements = [
        {'id': 'elem_1', 'text': 'E = mc² + ∫∫∫ρ(x,y,z)dxdydz'}
    ]
    
    groups_text, filtered_groups, optimal_duration = builder.build_adaptive_groups_section(
        semantic_map, ocr_elements
    )
    
    adaptive_instructions = builder.generate_adaptive_instructions(
        semantic_map,
        {'content_type': 'mathematical'},
        len(filtered_groups)
    )
    
    print(f"Optimal duration: {optimal_duration}s")
    print(f"Instructions preview: {adaptive_instructions[:200]}...")
    
    # Проверки
    assert optimal_duration >= 25, f"Complex content needs >=25s, got {optimal_duration}s"
    assert 'COMPLEX' in adaptive_instructions or 'step-by-step' in adaptive_instructions.lower(), \
        "Should mention complexity handling"
    print("✅ Test 3 PASSED")


def test_group_importance_ranking():
    """Тест ранжирования групп по важности"""
    print("\n=== TEST 4: Group Importance Ranking ===")
    
    builder = AdaptivePromptBuilder()
    
    groups = [
        {
            'id': 'footer',
            'type': 'footer',
            'priority': 'low',
            'educational_intent': 'N/A',
            'element_ids': ['e1'],
            'reading_order': [10]
        },
        {
            'id': 'main_title',
            'type': 'title',
            'priority': 'high',
            'educational_intent': 'Main concept',
            'element_ids': ['e2', 'e3', 'e4'],
            'reading_order': [1, 2, 3]
        },
        {
            'id': 'example',
            'type': 'example',
            'priority': 'medium',
            'educational_intent': 'Illustrate',
            'element_ids': ['e5'],
            'reading_order': [5]
        }
    ]
    
    scores = []
    for group in groups:
        score = builder._calculate_group_importance(group)
        scores.append((score, group['id']))
        print(f"Group '{group['id']}': importance = {score:.2f}")
    
    # Сортируем по важности
    scores.sort(reverse=True, key=lambda x: x[0])
    
    # Проверки
    assert scores[0][1] == 'main_title', "Title должен быть самым важным"
    assert scores[-1][1] == 'footer', "Footer должен быть наименее важным"
    print("✅ Test 4 PASSED")


def test_explanation_depth_assignment():
    """Тест назначения уровней детализации"""
    print("\n=== TEST 5: Explanation Depth Assignment ===")
    
    builder = AdaptivePromptBuilder()
    
    groups = [
        {'id': 'g1', 'type': 'title', 'priority': 'high'},
        {'id': 'g2', 'type': 'key_point', 'priority': 'high'},
        {'id': 'g3', 'type': 'example', 'priority': 'medium'},
        {'id': 'g4', 'type': 'content', 'priority': 'low'}
    ]
    
    # Test high density
    groups_with_depth = builder._assign_explanation_depth(groups, 'high', 'medium')
    print("\nHigh density depths:")
    for group, depth in groups_with_depth:
        print(f"  {group['id']}: {depth}")
    
    # Первая high-priority группа должна быть DETAILED
    assert groups_with_depth[0][1] == 'DETAILED', "First high-priority should be DETAILED"
    
    # Test low density
    groups_with_depth = builder._assign_explanation_depth(groups, 'low', 'easy')
    print("\nLow density depths:")
    for group, depth in groups_with_depth:
        print(f"  {group['id']}: {depth}")
    
    # При low density больше групп должны быть DETAILED
    detailed_count = sum(1 for _, depth in groups_with_depth if depth == 'DETAILED')
    assert detailed_count >= 2, "Low density should have more DETAILED explanations"
    
    print("✅ Test 5 PASSED")


if __name__ == '__main__':
    print("="*60)
    print("Testing AdaptivePromptBuilder")
    print("="*60)
    
    try:
        test_high_density_slide()
        test_low_density_slide()
        test_complex_cognitive_load()
        test_group_importance_ranking()
        test_explanation_depth_assignment()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
