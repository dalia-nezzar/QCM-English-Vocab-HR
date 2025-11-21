import streamlit as st
import json
import random
from difflib import SequenceMatcher

# Configuration de la page
st.set_page_config(page_title="Quiz Vocabulaire Professionnel", page_icon="📚", layout="wide")

# Fonction pour charger le vocabulaire
@st.cache_data
def load_vocabulary():
    with open('vocab.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['vocabulary']

# Fonction pour vérifier la similarité entre deux chaînes
def similarity_score(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

# Fonction pour générer des questions
def generate_questions(vocab, num_questions=10):
    questions = []
    vocab_sample = random.sample(vocab, min(num_questions, len(vocab)))
    
    for item in vocab_sample:
        question_type = random.choice(['multiple_choice', 'single_choice', 'open_ended'])
        
        if question_type == 'multiple_choice':
            # Question à choix multiples (plusieurs bonnes réponses)
            correct_term = item['term']
            question = {
                'type': 'multiple_choice',
                'question': f"Quelles affirmations sont vraies concernant '{correct_term}'? (Plusieurs réponses possibles)",
                'correct_answers': [item['definition']],
                'options': [item['definition']]
            }
            
            # Ajouter des distracteurs
            other_items = [v for v in vocab if v['term'] != correct_term]
            distractors = random.sample(other_items, min(3, len(other_items)))
            question['options'].extend([d['definition'] for d in distractors])
            random.shuffle(question['options'])
            questions.append(question)
            
        elif question_type == 'single_choice':
            # Question à choix unique
            correct_term = item['term']
            question = {
                'type': 'single_choice',
                'question': f"Quelle est la définition de '{correct_term}'?",
                'correct_answer': item['definition'],
                'options': [item['definition']]
            }
            
            # Ajouter des distracteurs
            other_items = [v for v in vocab if v['term'] != correct_term]
            distractors = random.sample(other_items, min(3, len(other_items)))
            question['options'].extend([d['definition'] for d in distractors])
            random.shuffle(question['options'])
            questions.append(question)
            
        else:  # open_ended
            # Question ouverte
            question = {
                'type': 'open_ended',
                'question': f"Définissez le terme '{item['term']}'",
                'correct_answer': item['definition'],
                'term': item['term']
            }
            questions.append(question)
    
    return questions

# Initialisation de la session
if 'questions' not in st.session_state:
    vocab = load_vocabulary()
    st.session_state.questions = generate_questions(vocab, 10)
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.answers = {}
    st.session_state.quiz_finished = False

# Interface principale
st.title("📚 Quiz de Vocabulaire Professionnel")
st.markdown("---")

# Barre de progression
if not st.session_state.quiz_finished:
    progress = st.session_state.current_question / len(st.session_state.questions)
    st.progress(progress)
    st.write(f"Question {st.session_state.current_question + 1} sur {len(st.session_state.questions)}")
    st.markdown("---")

# Affichage des questions
if not st.session_state.quiz_finished:
    question = st.session_state.questions[st.session_state.current_question]
    
    st.subheader(question['question'])
    st.write("")
    
    if question['type'] == 'multiple_choice':
        st.info("💡 Sélectionnez toutes les réponses correctes")
        selected_options = []
        for i, option in enumerate(question['options']):
            if st.checkbox(option, key=f"mc_{st.session_state.current_question}_{i}"):
                selected_options.append(option)
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ Valider", use_container_width=True):
                correct = set(selected_options) == set(question['correct_answers'])
                st.session_state.answers[st.session_state.current_question] = {
                    'user_answer': selected_options,
                    'correct': correct
                }
                if correct:
                    st.session_state.score += 1
                    st.success("✅ Correct !")
                else:
                    st.error(f"❌ Incorrect. La bonne réponse était : {question['correct_answers'][0]}")
                st.session_state.current_question += 1
                if st.session_state.current_question >= len(st.session_state.questions):
                    st.session_state.quiz_finished = True
                st.rerun()
    
    elif question['type'] == 'single_choice':
        st.info("💡 Sélectionnez une seule réponse")
        selected_option = st.radio(
            "Choisissez votre réponse :",
            question['options'],
            key=f"sc_{st.session_state.current_question}"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ Valider", use_container_width=True):
                correct = selected_option == question['correct_answer']
                st.session_state.answers[st.session_state.current_question] = {
                    'user_answer': selected_option,
                    'correct': correct
                }
                if correct:
                    st.session_state.score += 1
                    st.success("✅ Correct !")
                else:
                    st.error(f"❌ Incorrect. La bonne réponse était : {question['correct_answer']}")
                st.session_state.current_question += 1
                if st.session_state.current_question >= len(st.session_state.questions):
                    st.session_state.quiz_finished = True
                st.rerun()
    
    else:  # open_ended
        st.info("💡 Écrivez votre réponse (au moins 80% de similarité requise)")
        user_answer = st.text_area(
            "Votre réponse :",
            key=f"oe_{st.session_state.current_question}",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ Valider", use_container_width=True):
                if user_answer.strip():
                    similarity = similarity_score(user_answer, question['correct_answer'])
                    correct = similarity >= 0.8
                    
                    st.session_state.answers[st.session_state.current_question] = {
                        'user_answer': user_answer,
                        'correct': correct,
                        'similarity': similarity
                    }
                    
                    if correct:
                        st.session_state.score += 1
                        st.success(f"✅ Correct ! (Similarité : {similarity*100:.1f}%)")
                    else:
                        st.error(f"❌ Pas assez proche (Similarité : {similarity*100:.1f}%)")
                        st.info(f"💡 Réponse attendue : {question['correct_answer']}")
                    
                    st.session_state.current_question += 1
                    if st.session_state.current_question >= len(st.session_state.questions):
                        st.session_state.quiz_finished = True
                    st.rerun()
                else:
                    st.warning("⚠️ Veuillez entrer une réponse")

else:
    # Écran de résultats
    st.balloons()
    st.success("🎉 Quiz terminé !")
    
    score_percentage = (st.session_state.score / len(st.session_state.questions)) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{st.session_state.score}/{len(st.session_state.questions)}")
    with col2:
        st.metric("Pourcentage", f"{score_percentage:.1f}%")
    with col3:
        if score_percentage >= 80:
            st.metric("Résultat", "🏆 Excellent")
        elif score_percentage >= 60:
            st.metric("Résultat", "👍 Bien")
        else:
            st.metric("Résultat", "📚 À revoir")
    
    st.markdown("---")
    
    # Détails des réponses
    with st.expander("📋 Voir le détail de vos réponses"):
        for i, q in enumerate(st.session_state.questions):
            answer = st.session_state.answers.get(i)
            if answer:
                if answer['correct']:
                    st.success(f"✅ Question {i+1}: {q['question']}")
                else:
                    st.error(f"❌ Question {i+1}: {q['question']}")
                    if q['type'] == 'open_ended':
                        st.write(f"Votre réponse : {answer['user_answer']}")
                        st.write(f"Similarité : {answer.get('similarity', 0)*100:.1f}%")
    
    # Bouton pour recommencer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Recommencer le quiz", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Sidebar avec informations
with st.sidebar:
    st.header("ℹ️ Instructions")
    st.write("""
    Ce quiz teste vos connaissances sur le vocabulaire professionnel en anglais.
    
    **Types de questions :**
    - 🔘 Choix unique
    - ☑️ Choix multiples
    - ✍️ Réponse ouverte (80% de similarité requise)
    
    **Bonne chance !** 🍀
    """)
    
    st.markdown("---")
    st.caption("Quiz créé avec Streamlit 🎈")