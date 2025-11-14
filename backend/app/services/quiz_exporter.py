"""
Quiz Export Service
Export quizzes to various formats: JSON, Moodle XML, HTML
"""
import logging
from typing import Dict, Any
import json
import html

logger = logging.getLogger(__name__)

class QuizExporter:
    """Export quizzes to various formats"""
    
    @staticmethod
    def export(quiz: Dict[str, Any], format: str) -> str:
        """
        Export quiz to specified format
        
        Args:
            quiz: Quiz data dict with questions and answers
            format: Export format (json, moodle, html)
            
        Returns:
            Exported content as string
        """
        exporters = {
            "json": QuizExporter._to_json,
            "moodle": QuizExporter._to_moodle_xml,
            "moodle_xml": QuizExporter._to_moodle_xml,
            "html": QuizExporter._to_html,
        }
        
        exporter = exporters.get(format.lower())
        if not exporter:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"📤 Exporting quiz to {format}")
        return exporter(quiz)
    
    @staticmethod
    def _to_json(quiz: Dict[str, Any]) -> str:
        """Export as JSON"""
        return json.dumps(quiz, indent=2, default=str, ensure_ascii=False)
    
    @staticmethod
    def _to_moodle_xml(quiz: Dict[str, Any]) -> str:
        """
        Export as Moodle XML format
        Compatible with Moodle 3.x and 4.x
        """
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
        
        for i, question in enumerate(quiz.get('questions', [])):
            q_type = question.get('type', 'multiple_choice')
            
            if q_type == 'multiple_choice':
                xml += f'  <question type="multichoice">\n'
                xml += f'    <name><text>Q{i+1}</text></name>\n'
                xml += f'    <questiontext format="html">\n'
                xml += f'      <text><![CDATA[{html.escape(question.get("text", ""))}]]></text>\n'
                xml += f'    </questiontext>\n'
                xml += f'    <single>true</single>\n'
                xml += f'    <shuffleanswers>true</shuffleanswers>\n'
                
                for answer in question.get('answers', []):
                    fraction = "100" if answer.get('is_correct') else "0"
                    xml += f'    <answer fraction="{fraction}" format="html">\n'
                    xml += f'      <text><![CDATA[{html.escape(answer.get("text", ""))}]]></text>\n'
                    xml += f'    </answer>\n'
                
                if question.get('explanation'):
                    xml += f'    <generalfeedback format="html">\n'
                    xml += f'      <text><![CDATA[{html.escape(question["explanation"])}]]></text>\n'
                    xml += f'    </generalfeedback>\n'
                
                xml += f'  </question>\n'
            
            elif q_type == 'multiple_select':
                xml += f'  <question type="multichoice">\n'
                xml += f'    <name><text>Q{i+1}</text></name>\n'
                xml += f'    <questiontext format="html">\n'
                xml += f'      <text><![CDATA[{html.escape(question.get("text", ""))}]]></text>\n'
                xml += f'    </questiontext>\n'
                xml += f'    <single>false</single>\n'
                xml += f'    <shuffleanswers>true</shuffleanswers>\n'
                
                correct_count = sum(1 for a in question.get('answers', []) if a.get('is_correct'))
                fraction_per_correct = 100 / correct_count if correct_count > 0 else 0
                
                for answer in question.get('answers', []):
                    if answer.get('is_correct'):
                        fraction = f"{fraction_per_correct:.2f}"
                    else:
                        fraction = "0"
                    
                    xml += f'    <answer fraction="{fraction}" format="html">\n'
                    xml += f'      <text><![CDATA[{html.escape(answer.get("text", ""))}]]></text>\n'
                    xml += f'    </answer>\n'
                
                if question.get('explanation'):
                    xml += f'    <generalfeedback format="html">\n'
                    xml += f'      <text><![CDATA[{html.escape(question["explanation"])}]]></text>\n'
                    xml += f'    </generalfeedback>\n'
                
                xml += f'  </question>\n'
            
            elif q_type == 'true_false':
                xml += f'  <question type="truefalse">\n'
                xml += f'    <name><text>Q{i+1}</text></name>\n'
                xml += f'    <questiontext format="html">\n'
                xml += f'      <text><![CDATA[{html.escape(question.get("text", ""))}]]></text>\n'
                xml += f'    </questiontext>\n'
                
                # Find correct answer
                correct_answer = next(
                    (a for a in question.get('answers', []) if a.get('is_correct')),
                    None
                )
                
                if correct_answer:
                    answer_text = correct_answer.get('text', '').lower()
                    is_true = 'true' in answer_text or 'верно' in answer_text or 'да' in answer_text
                    xml += f'    <answer fraction="100" format="moodle_auto_format">\n'
                    xml += f'      <text>{"true" if is_true else "false"}</text>\n'
                    xml += f'    </answer>\n'
                
                if question.get('explanation'):
                    xml += f'    <generalfeedback format="html">\n'
                    xml += f'      <text><![CDATA[{html.escape(question["explanation"])}]]></text>\n'
                    xml += f'    </generalfeedback>\n'
                
                xml += f'  </question>\n'
            
            elif q_type == 'short_answer':
                xml += f'  <question type="shortanswer">\n'
                xml += f'    <name><text>Q{i+1}</text></name>\n'
                xml += f'    <questiontext format="html">\n'
                xml += f'      <text><![CDATA[{html.escape(question.get("text", ""))}]]></text>\n'
                xml += f'    </questiontext>\n'
                xml += f'    <usecase>0</usecase>\n'
                
                for answer in question.get('answers', []):
                    if answer.get('is_correct'):
                        xml += f'    <answer fraction="100" format="moodle_auto_format">\n'
                        xml += f'      <text>{html.escape(answer.get("text", ""))}</text>\n'
                        xml += f'    </answer>\n'
                
                if question.get('explanation'):
                    xml += f'    <generalfeedback format="html">\n'
                    xml += f'      <text><![CDATA[{html.escape(question["explanation"])}]]></text>\n'
                    xml += f'    </generalfeedback>\n'
                
                xml += f'  </question>\n'
        
        xml += '</quiz>'
        return xml
    
    @staticmethod
    def _to_html(quiz: Dict[str, Any]) -> str:
        """
        Export as interactive HTML page
        Standalone HTML file with embedded CSS and JavaScript
        """
        title = html.escape(quiz.get('title', 'Quiz'))
        description = html.escape(quiz.get('description', ''))
        
        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .content {{ padding: 40px; }}
        .question {{
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }}
        .question-number {{
            color: #667eea;
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .question-text {{
            font-size: 1.2em;
            font-weight: 500;
            margin-bottom: 20px;
            color: #2d3748;
        }}
        .answer {{
            padding: 15px;
            margin: 10px 0;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .answer:hover {{ border-color: #667eea; background: #f7fafc; }}
        .answer.selected {{ border-color: #667eea; background: #edf2f7; }}
        .answer.correct {{ border-color: #48bb78; background: #f0fff4; }}
        .answer.incorrect {{ border-color: #f56565; background: #fff5f5; }}
        .explanation {{
            margin-top: 15px;
            padding: 15px;
            background: #edf2f7;
            border-left: 3px solid #4299e1;
            border-radius: 4px;
            display: none;
        }}
        .explanation.show {{ display: block; }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }}
        .button:active {{ transform: translateY(0); }}
        .results {{
            text-align: center;
            padding: 40px;
            display: none;
        }}
        .results.show {{ display: block; }}
        .score {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #e2e8f0;
        }}
        @media (max-width: 640px) {{
            .header {{ padding: 30px 20px; }}
            .content {{ padding: 20px; }}
            .question {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{description}</p>
        </div>
        
        <div class="content">
            <div id="quiz">
"""
        
        # Generate questions HTML
        for i, question in enumerate(quiz.get('questions', [])):
            q_num = i + 1
            q_text = html.escape(question.get('text', ''))
            q_type = question.get('type', 'multiple_choice')
            q_explanation = html.escape(question.get('explanation', ''))
            
            html_content += f"""
                <div class="question" data-question="{q_num}">
                    <div class="question-number">Вопрос {q_num}</div>
                    <div class="question-text">{q_text}</div>
                    <div class="answers">
"""
            
            for j, answer in enumerate(question.get('answers', [])):
                a_text = html.escape(answer.get('text', ''))
                is_correct = 'true' if answer.get('is_correct') else 'false'
                input_type = 'checkbox' if q_type == 'multiple_select' else 'radio'
                
                html_content += f"""
                        <div class="answer" data-correct="{is_correct}" data-question="{q_num}" data-answer="{j}">
                            <input type="{input_type}" name="q{q_num}" value="{j}" style="margin-right: 10px;">
                            {a_text}
                        </div>
"""
            
            html_content += """
                    </div>
"""
            
            if q_explanation:
                html_content += f"""
                    <div class="explanation" data-question="{q_num}">
                        <strong>💡 Объяснение:</strong> {q_explanation}
                    </div>
"""
            
            html_content += """
                </div>
"""
        
        html_content += f"""
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <button class="button" onclick="checkAnswers()">Проверить ответы</button>
                <button class="button" onclick="resetQuiz()" style="margin-left: 10px; background: #718096;">Сбросить</button>
            </div>
            
            <div class="results" id="results">
                <h2>Результаты</h2>
                <div class="score" id="score"></div>
                <p id="message"></p>
                <button class="button" onclick="resetQuiz()" style="margin-top: 20px;">Пройти ещё раз</button>
            </div>
        </div>
        
        <div class="footer">
            <p>Создано с помощью Slide Speaker</p>
        </div>
    </div>
    
    <script>
        // Handle answer selection
        document.querySelectorAll('.answer').forEach(answer => {{
            answer.addEventListener('click', function() {{
                const input = this.querySelector('input');
                const questionNum = this.dataset.question;
                
                if (input.type === 'radio') {{
                    // Clear other selections for radio buttons
                    document.querySelectorAll(`.answer[data-question="${{questionNum}}"]`).forEach(a => {{
                        a.classList.remove('selected');
                    }});
                }}
                
                input.checked = !input.checked;
                this.classList.toggle('selected', input.checked);
            }});
        }});
        
        function checkAnswers() {{
            let correct = 0;
            let total = {len(quiz.get('questions', []))};
            
            document.querySelectorAll('.question').forEach(question => {{
                const questionNum = question.dataset.question;
                const answers = question.querySelectorAll('.answer');
                const explanation = question.querySelector('.explanation');
                
                let questionCorrect = true;
                
                answers.forEach(answer => {{
                    const input = answer.querySelector('input');
                    const isCorrect = answer.dataset.correct === 'true';
                    
                    if (input.checked) {{
                        if (isCorrect) {{
                            answer.classList.add('correct');
                        }} else {{
                            answer.classList.add('incorrect');
                            questionCorrect = false;
                        }}
                    }} else if (isCorrect) {{
                        answer.classList.add('correct');
                        questionCorrect = false;
                    }}
                }});
                
                if (questionCorrect) correct++;
                if (explanation) explanation.classList.add('show');
            }});
            
            // Show results
            const percentage = Math.round((correct / total) * 100);
            document.getElementById('score').textContent = `${{correct}} / ${{total}} (${{percentage}}%)`;
            
            let message = '';
            if (percentage >= 90) message = '🎉 Отлично! Вы отлично усвоили материал!';
            else if (percentage >= 70) message = '👍 Хорошо! Есть небольшие пробелы.';
            else if (percentage >= 50) message = '📚 Неплохо, но стоит повторить материал.';
            else message = '💪 Нужно больше практики!';
            
            document.getElementById('message').textContent = message;
            document.getElementById('results').classList.add('show');
            
            // Scroll to results
            document.getElementById('results').scrollIntoView({{ behavior: 'smooth' }});
        }}
        
        function resetQuiz() {{
            document.querySelectorAll('.answer').forEach(answer => {{
                answer.classList.remove('selected', 'correct', 'incorrect');
                const input = answer.querySelector('input');
                input.checked = false;
            }});
            
            document.querySelectorAll('.explanation').forEach(exp => {{
                exp.classList.remove('show');
            }});
            
            document.getElementById('results').classList.remove('show');
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
    </script>
</body>
</html>"""
        
        return html_content
