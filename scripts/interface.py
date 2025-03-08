# Script: `.\scripts\interface.py`

# Imports...
import gradio as gr
from gradio import themes
import re, os, json, pyperclip, yake, random, asyncio
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from queue import Queue
import scripts.temporary as temporary
from scripts.temporary import (
    USER_COLOR, THINK_COLOR, RESPONSE_COLOR, SEPARATOR, MID_SEPARATOR,
    ALLOWED_EXTENSIONS, N_CTX, VRAM_SIZE, SELECTED_GPU, SELECTED_CPU,
    current_model_settings, N_GPU_LAYERS, VRAM_OPTIONS, REPEAT_OPTIONS,
    REPEAT_PENALTY, MLOCK, HISTORY_DIR, BATCH_OPTIONS, N_BATCH, MODEL_FOLDER,
    MODEL_NAME, STATUS_TEXTS, CTX_OPTIONS, RP_LOCATION, USER_PC_NAME, USER_PC_ROLE,
    AI_NPC_NAME, AI_NPC_ROLE, SESSION_ACTIVE, TOT_VARIATIONS,
    MAX_HISTORY_SLOTS, MAX_ATTACH_SLOTS, HISTORY_SLOT_OPTIONS, ATTACH_SLOT_OPTIONS,
    BACKEND_TYPE, STREAM_OUTPUT
)
from scripts import utility
from scripts.utility import (
    delete_all_session_vectorstores, create_session_vectorstore, web_search, get_saved_sessions,
    load_session_history, save_session_history, load_and_chunk_documents,
    get_available_gpus, create_session_vectorstore, save_config
)
from scripts.models import (
    get_response_stream, get_available_models, unload_models, get_model_settings,
    context_injector, inspect_model, load_models
)
from langchain_core.documents import Document



# Functions...
def set_loading_status():
    return "Loading model..."

def format_response(output: str) -> str:
    formatted = []
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', output, re.DOTALL)
    for lang, code in code_blocks:
        lexer = get_lexer_by_name(lang, stripall=True)
        formatted_code = highlight(code, lexer, HtmlFormatter())
        output = output.replace(f'```{lang}\n{code}```', formatted_code)
    return f'<span style="color: {RESPONSE_COLOR}">{output}</span>'

def select_directory():
    print("Opening directory selection dialog...")  # Debug print
    root = tk.Tk()
    root.withdraw()  # Hide the Tkinter window
    initial_dir = r"C:\Program_Filez\Text-Gradio-Gguf\Text-Gradio-Gguf-main\models"
    if not os.path.exists(initial_dir):
        initial_dir = os.path.expanduser("~")  # Fallback to home directory
    path = filedialog.askdirectory(initialdir=initial_dir)
    root.destroy()
    if path:
        print(f"Selected path: {path}")  # Debug print
        return path
    else:
        print("No directory selected")  # Debug print
        return None

def web_search_trigger(query):
    try:
        result = utility.web_search(query)
        return result if result else "No results found"
    except Exception as e:
        return f"Error: {str(e)}"

def save_rp_settings(rp_location, user_name, user_role, ai_npc, ai_npc_role):
    from scripts import temporary
    config_path = Path("data/persistent.json")
    
    # Update temporary variables
    temporary.RP_LOCATION = rp_location
    temporary.USER_PC_NAME = user_name
    temporary.USER_PC_ROLE = user_role
    temporary.AI_NPC_NAME = ai_npc
    temporary.AI_NPC_ROLE = ai_npc_role
    
    # Save to config file and return updated values
    utility.save_config()
    return (
        rp_location, user_name, user_role, ai_npc, ai_npc_role,
        rp_location, user_name, user_role, ai_npc, ai_npc_role  # Sync both sides
    )

def process_uploaded_files(files, loaded_files, models_loaded):
    from scripts.utility import create_session_vectorstore
    import scripts.temporary as temporary
    if not models_loaded:
        return "Error: Load a model first.", loaded_files
    
    max_files = temporary.MAX_ATTACH_SLOTS
    if len(loaded_files) >= max_files:
        return f"Max files ({max_files}) reached.", loaded_files
    
    new_files = [f for f in files if f not in loaded_files]
    available_slots = max_files - len(loaded_files)
    loaded_files.extend(new_files[:available_slots])
    
    session_vectorstore = create_session_vectorstore(loaded_files)
    context_injector.set_session_vectorstore(session_vectorstore)
    
    return f"Processed {min(len(new_files), available_slots)} new files.", loaded_files

def eject_file(loaded_files, slot_index):
    from scripts.utility import create_session_vectorstore
    from pathlib import Path
    if 0 <= slot_index < len(loaded_files):
        removed_file = loaded_files.pop(slot_index)
        try:
            Path(removed_file).unlink()
        except Exception as e:
            print(f"Error unlinking file: {e}")
        session_vectorstore = create_session_vectorstore(loaded_files)
        context_injector.set_session_vectorstore(session_vectorstore)
        status_msg = f"Ejected {Path(removed_file).name}"
    else:
        status_msg = "No file to eject"
    updates = update_file_slot_ui(loaded_files)
    return [loaded_files, status_msg] + updates

def remove_all_attachments(loaded_files):
    from scripts.utility import create_session_vectorstore
    loaded_files = []
    session_vectorstore = create_session_vectorstore(loaded_files)
    context_injector.set_session_vectorstore(session_vectorstore)
    status_msg = "All attachments removed."
    updates = update_file_slot_ui(loaded_files)  # Now returns all updates
    return [loaded_files, status_msg] + updates

def toggle_rpg_settings(showing_rpg_right):
 new_showing_rpg_right = not showing_rpg_right
 toggle_label = "Show File Attachments" if new_showing_rpg_right else "Show RPG Settings"
 return (
 gr.update(visible=True, value=toggle_label), # toggle_rpg_settings_btn
 gr.update(visible=not new_showing_rpg_right), # file_attachments_group
 gr.update(visible=new_showing_rpg_right), # rpg_settings_group
 new_showing_rpg_right # Update state
 )

def handle_slot_click(slot_index, loaded_files, rag_max_docs):
    if slot_index < len(loaded_files):
        removed_file = loaded_files.pop(slot_index)
        try:
            Path(removed_file).unlink()
        except Exception as e:
            print(f"Error unlinking file: {e}")
        docs = load_and_chunk_documents([Path(f) for f in loaded_files])
        create_vectorstore(docs, "chat")
        status_msg = f"Ejected {Path(removed_file).name}"
    else:
        status_msg = "Click 'Attach Files' to add files."
    return [loaded_files, status_msg] + update_file_slot_ui(loaded_files, rag_max_docs)

def start_new_session():
    from scripts import temporary
    temporary.current_session_id = None
    temporary.session_label = ""
    temporary.SESSION_ACTIVE = True
    return [], "Type input and click Send to begin...", gr.update(interactive=True)

def load_session_by_index(index):
    sessions = utility.get_saved_sessions()
    if index < len(sessions):
        session_file = sessions[index]
        return utility.load_session_history(Path(HISTORY_DIR) / session_file)
    return [], "No session to load"

def copy_last_response(session_log):
    if session_log and session_log[-1]['role'] == 'assistant':
        response = session_log[-1]['content']
        clean_response = re.sub(r'<[^>]+>', '', response)
        pyperclip.copy(clean_response)
        return "AI Response copied to clipboard."
    return "No response available to copy."

def cancel_input():
    return True, gr.update(visible=True), gr.update(visible=False), "Input cancelled."

def shutdown_program(models_loaded):
    import time
    import sys
    
    if models_loaded:
        print("Shutting Down...")
        print("Unloading model...")
        unload_models()
        print("Model unloaded.")
    
    print("Closing Gradio server...")
    demo.close()
    print("Gradio server closed.")
    
    print()
    print()
    print("A program by Wiseman-Timelord")
    print()
    print("GitHub: github.com/wiseman-timelord")
    print("Website: wisetime.rf.gd")
    print()
    print()
    
    for i in range(5, 0, -1):
        print(f"\rExiting program in...{i}s", end='', flush=True)
        time.sleep(1)
    print()  # Adds a newline after the countdown for clean termination
    os._exit(0)

def update_mode_based_options(mode, showing_rpg_right):
    mode = mode.lower()
    is_rpg = mode == "rpg"
    
    if not is_rpg:
        showing_rpg_right = False  # Reset to show File Attachments when not in RPG mode
    
    if mode == "code":
        tot_visible = False
        web_visible = True   # Changed to True to enable web search visibility in Code mode
        file_visible = True
    elif is_rpg:
        tot_visible = False
        web_visible = False
        file_visible = True
    else:  # chat
        tot_visible = True
        web_visible = True
        file_visible = True
    
    toggle_visible = is_rpg  # Only show toggle in RPG mode
    toggle_label = "Show File Attachments" if showing_rpg_right else "Show RPG Settings"
    
    file_attachments_visible = not showing_rpg_right if is_rpg else True
    rpg_settings_visible = showing_rpg_right if is_rpg else False
    
    return [
        gr.update(visible=tot_visible),      # TOT checkbox
        gr.update(visible=web_visible),      # Web search
        gr.update(visible=file_visible),     # attach_files_btn
        gr.update(visible=toggle_visible, value=toggle_label),  # toggle_rpg_settings_btn
        gr.update(visible=file_attachments_visible),  # file_attachments_group
        gr.update(visible=rpg_settings_visible),      # rpg_settings_group
        showing_rpg_right                     # Update the state
    ]

def determine_operation_mode(model_name):
    if model_name == "Select_a_model...":
        return "Select models to enable mode detection."
    settings = get_model_settings(model_name)
    category = settings["category"]
    if category == "code":
        return "Code"
    elif category == "rpg":
        return "Rpg"
    elif category == "uncensored":
        return "Chat"
    return "Chat"

def update_model_based_options(model_name):
    """
    Update UI options based on the selected model.
    Handles cases where no model is selected or no models are found.
    """
    if model_name is None or model_name in ["Select_a_model...", "No models found"]:
        mode = "Chat"  # Default to Chat when no valid model is selected
        think_visible = False
        recommended = "Select a model"
    else:
        settings = get_model_settings(model_name)
        mode = settings["category"].capitalize()
        think_visible = settings["is_reasoning"]
        recommended = mode
    return [
        gr.update(value=mode),      # Set radio button to model’s category
        gr.update(visible=think_visible),  # Set Think Switch visibility
        gr.update(value=recommended),  # Set recommended_mode textbox
    ]

def update_dynamic_options(model_name, loaded_files_state, showing_rpg_right):
    if model_name == "Select_a_model...":
        mode = "Select models"
        settings = {"is_reasoning": False}
    else:
        settings = get_model_settings(model_name)
        mode = settings["category"].capitalize()
    
    think_visible = settings["is_reasoning"]
    
    if mode == "Code":
        tot_visible = False
        web_visible = True
        file_visible = True
    elif mode == "Rpg":
        tot_visible = False
        web_visible = False
        file_visible = True
    else:  # Chat mode
        tot_visible = True
        web_visible = True
        file_visible = True

    # Right column visibility logic
    toggle_visible = True  # Always visible for development
    toggle_label = "Show File Attachments" if showing_rpg_right else "Show RPG Settings"
    
    return [
        gr.update(visible=tot_visible),      # TOT checkbox
        gr.update(visible=web_visible),      # Web search
        gr.update(visible=think_visible),    # Think switch
        gr.update(value=mode),               # Theme status
        gr.update(visible=file_visible),     # attach_files_btn
        gr.update(visible=toggle_visible, value=toggle_label),  # toggle_rpg_settings_btn
        gr.update(visible=not showing_rpg_right),  # file_attachments_group
        gr.update(visible=showing_rpg_right),      # rpg_settings_group
        showing_rpg_right                          # Update the state
    ]

def update_file_slot_ui(loaded_files):
    from pathlib import Path
    import scripts.temporary as temporary
    button_updates = []
    for i in range(MAX_ATTACH_SLOTS):
        if i < temporary.MAX_ATTACH_SLOTS:
            if i < len(loaded_files):
                filename = Path(loaded_files[i]).name
                short_name = (filename[:13] + ".." if len(filename) > 15 else filename)
                label = f"{short_name}"
                variant = "secondary"
            else:
                label = "File Slot Free"
                variant = "primary"
            visible = True
        else:
            label = ""
            variant = "primary"
            visible = False
        button_updates.append(gr.update(value=label, visible=visible, variant=variant))
    attach_files_visible = len(loaded_files) < temporary.MAX_ATTACH_SLOTS
    return button_updates + [gr.update(visible=attach_files_visible)]

def update_rp_settings(rp_location, user_name, user_role, ai_npc, ai_npc_role):
    temporary.RP_LOCATION = rp_location
    temporary.USER_PC_NAME = user_name
    temporary.USER_PC_ROLE = user_role
    temporary.AI_NPC_NAME = ai_npc
    temporary.AI_NPC_ROLE = ai_npc_role
    return rp_location, user_name, user_role, ai_npc, ai_npc_role

def save_rpg_settings_to_json():
    config_path = Path("data/persistent.json")
    if config_path.exists():
        with open(config_path, "r+") as f:
            config = json.load(f)
            config["rp_settings"] = {
                "rp_location": temporary.RP_LOCATION,
                "user_name": temporary.USER_PC_NAME,
                "user_role": temporary.USER_PC_ROLE,
                "ai_npc": temporary.AI_NPC_NAME,
                "ai_npc_role": temporary.AI_NPC_ROLE
            }
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()
        return "RPG settings saved to persistent.json"
    else:
        return "Configuration file not found."

def update_session_buttons():
    import scripts.temporary as temporary
    sessions = utility.get_saved_sessions()
    button_updates = []
    for i in range(MAX_HISTORY_SLOTS):
        if i < temporary.MAX_HISTORY_SLOTS:
            if i < len(sessions):
                session_path = Path(HISTORY_DIR) / sessions[i]
                try:
                    label, _ = utility.load_session_history(session_path)
                    btn_label = f"{label}" if label else f"Session {i+1}"
                except Exception:
                    btn_label = f"Session {i+1}"
            else:
                btn_label = "History Slot Empty"
            button_updates.append(gr.update(value=btn_label, visible=True))
        else:
            button_updates.append(gr.update(visible=False))
    return button_updates

def update_left_panel_visibility(mode, showing_rpg_settings):
    is_rpg_mode = (mode.lower() == "rpg")
    if is_rpg_mode and showing_rpg_settings:
        return gr.update(visible=False), gr.update(visible=True)
    else:
        return gr.update(visible=True), gr.update(visible=False)

# Button (keep buttons somewhere above cha_interfac & launc_interfac)
def update_action_button(phase):
    """
    Update the action button's label and variant based on the current interaction phase.

    Args:
        phase (str): The current phase of interaction.

    Returns:
        gradio.update: An update object for the button with the appropriate label and variant.
    """
    if phase == "waiting_for_input":
        return gr.update(value="Send Input", variant="secondary")
    elif phase == "afterthought_countdown":
        return gr.update(value="Cancel Input", variant="stop")
    elif phase == "generating_response":
        return gr.update(value="Cancel Response", variant="stop")
    else:
        return gr.update(value="Unknown Phase", variant="primary")

def set_loading_status():
    return "Loading model..."

# chat_interface function signature
# Script: `.\scripts\interface.py`

async def chat_interface(user_input, session_log, tot_enabled, loaded_files_state, disable_think, 
                        rp_location, user_name, user_role, ai_npc, cancel_flag, mode_selection, 
                        web_search_enabled, models_loaded, interaction_phase):
    from scripts import temporary, utility, models
    from scripts.temporary import STATUS_TEXTS, MODEL_NAME, SESSION_ACTIVE, TOT_VARIATIONS
    import asyncio
    
    # Check if model is loaded
    if not models_loaded:
        yield session_log, "Please load a model first.", gr.update(), cancel_flag, loaded_files_state, interaction_phase
        return
    
    # Automatically start a new session if none is active
    if not temporary.SESSION_ACTIVE:
        temporary.current_session_id = None
        temporary.session_label = ""
        temporary.SESSION_ACTIVE = True
        session_log = []
        yield session_log, "New session started.", gr.update(), cancel_flag, loaded_files_state, interaction_phase
        await asyncio.sleep(0.1)
    
    # Validate input
    if not user_input.strip():
        yield session_log, "No input provided.", gr.update(), cancel_flag, loaded_files_state, interaction_phase
        return

    # Append user input with "User:" prefix
    session_log.append({'role': 'user', 'content': f"User:\n{user_input}"})
    session_log.append({'role': 'assistant', 'content': "Afterthought countdown... "})

    # Transition to afterthought_countdown phase
    interaction_phase = "afterthought_countdown"
    yield session_log, "Processing...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase

    # Countdown logic
    if temporary.AFTERTHOUGHT_TIME:
        num_lines = len(user_input.split('\n'))
        countdown_seconds = 6 if num_lines >= 10 else 4 if num_lines >= 5 else 2
    else:
        countdown_seconds = 1

    for i in range(countdown_seconds, -1, -1):  # Count down to 0
        session_log[-1]['content'] = f"Afterthought countdown... {i}s"
        yield session_log, "Counting down...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
        await asyncio.sleep(1)
        if cancel_flag:
            session_log[-1]['content'] = "Input cancelled."
            interaction_phase = "waiting_for_input"
            yield session_log, "Input cancelled.", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
            return

    # Transition to generating_response phase with CLI execution message
    session_log[-1]['content'] = "Afterthought countdown... 0s ...Executing CLI llama-cli"
    interaction_phase = "generating_response"
    yield session_log, "Generating...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase

    # Generate response
    settings = models.get_model_settings(MODEL_NAME)
    mode = mode_selection.lower()

    if loaded_files_state:
        session_vectorstore = utility.create_session_vectorstore(loaded_files_state)
        models.context_injector.set_session_vectorstore(session_vectorstore)

    prompt = user_input
    if web_search_enabled and mode in ["chat", "code"]:
        session_log[-1]['content'] = "Performing web search..."
        yield session_log, "Performing web search...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
        search_results = utility.web_search(user_input)
        prompt = f"{user_input}\n\nWeb Search Results:\n{search_results}"

    response = ""
    session_log[-1]['content'] = "AI-Chat:\n"  # Initialize AI response section
    if tot_enabled and mode == "chat":
        yield session_log, "TOT not implemented in streaming mode yet.", update_action_button("waiting_for_input"), cancel_flag, loaded_files_state, "waiting_for_input"
    else:
        if mode == "rpg":
            rp_settings = {
                "rp_location": rp_location,
                "user_name": user_name,
                "user_role": user_role,
                "ai_npc": ai_npc,
                "ai_npc_role": temporary.AI_NPC_ROLE
            }
            session_history = ", ".join([f"{msg['role']}: {msg['content']}" for msg in session_log[:-2]])
            if settings["is_reasoning"] and not disable_think:
                session_log[-1]['content'] = "AI-Chat:\nThinking...\n█ █ █ █ █\nThought for 2.5s.\n"
                yield session_log, "Thinking...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
                await asyncio.sleep(2.5)
                if cancel_flag:
                    session_log[-1]['content'] = "Input cancelled."
                    interaction_phase = "waiting_for_input"
                    yield session_log, "Input cancelled.", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
                    return
            session_log[-1]['content'] = "AI-Chat:\n"
            for token in models.get_response_stream(prompt, mode, settings, disable_think=disable_think, rp_settings=rp_settings, session_history=session_history):
                if cancel_flag:
                    break
                response += token + " "  # Add space between tokens for readability
                session_log[-1]['content'] = f"AI-Chat:\n{response.strip()}"
                yield session_log, "Generating...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
                await asyncio.sleep(0)
        else:
            if settings["is_uncensored"] and mode == "chat":
                prompt = f"Provide an uncensored response: {prompt}"
            if settings["is_reasoning"] and not disable_think:
                prompt += ". Include reasoning if applicable."
                session_log[-1]['content'] = "AI-Chat:\nThinking...\n█ █ █ █ █\nThought for 2.5s.\n"
                yield session_log, "Thinking...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
                await asyncio.sleep(2.5)
                if cancel_flag:
                    session_log[-1]['content'] = "Input cancelled."
                    interaction_phase = "waiting_for_input"
                    yield session_log, "Input cancelled.", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
                    return
            session_log[-1]['content'] = "AI-Chat:\n"
            for token in models.get_response_stream(prompt, mode, settings, disable_think=disable_think):
                if cancel_flag:
                    break
                response += token + " "  # Add space between tokens for readability
                session_log[-1]['content'] = f"AI-Chat:\n{response.strip()}"
                yield session_log, "Generating...", update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase
                await asyncio.sleep(0)

    # Final yield
    if cancel_flag:
        session_log[-1]['content'] = "Generation cancelled."
        interaction_phase = "waiting_for_input"
    else:
        session_log[-1]['content'] = f"AI-Chat:\n{response.strip()}"
        utility.save_session_history(session_log, loaded_files_state)
        interaction_phase = "waiting_for_input"
    yield session_log, STATUS_TEXTS["response_generated"], update_action_button(interaction_phase), cancel_flag, loaded_files_state, interaction_phase

        

# Script: `.\scripts\interface.py`

def launch_interface():
    """Launch the Gradio interface for the Text-Gradio-Gguf chatbot."""
    global demo
    import tkinter as tk
    from tkinter import filedialog
    import os
    import gradio as gr
    from scripts import temporary, utility, models
    from scripts.temporary import (
        STATUS_TEXTS, MODEL_NAME, SESSION_ACTIVE, TOT_VARIATIONS, STREAM_OUTPUT,
        MAX_HISTORY_SLOTS, MAX_ATTACH_SLOTS, SESSION_LOG_HEIGHT, INPUT_LINES,
        AFTERTHOUGHT_TIME, MODEL_FOLDER, N_CTX, N_BATCH, TEMPERATURE, REPEAT_PENALTY,
        VRAM_SIZE, SELECTED_GPU, SELECTED_CPU, MLOCK, BACKEND_TYPE,
        RP_LOCATION, USER_PC_NAME, USER_PC_ROLE, AI_NPC_NAME, AI_NPC_ROLE,
        ALLOWED_EXTENSIONS, VRAM_OPTIONS, CTX_OPTIONS, BATCH_OPTIONS, TEMP_OPTIONS,
        REPEAT_OPTIONS, HISTORY_SLOT_OPTIONS, SESSION_LOG_HEIGHT_OPTIONS,
        INPUT_LINES_OPTIONS, ATTACH_SLOT_OPTIONS
    )

    # Cache models and set default
    available_models = models.get_available_models() or ["No models found"]
    default_model = temporary.MODEL_NAME if temporary.MODEL_NAME in available_models else "Select_a_model..."

    with gr.Blocks(title="Chat-Gradio-Gguf", css=".scrollable{overflow-y:auto}.send-button{background-color:green!important;color:white!important;height:80px!important}.double-height{height:80px!important}.clean-elements{gap:4px!important;margin-bottom:4px!important}.clean-elements-normbot{gap:4px!important;margin-bottom:10px!important}") as demo:
        # States
        states = dict(
            loaded_files=gr.State([]),
            models_loaded=gr.State(False),
            showing_rpg_right=gr.State(False),
            cancel_flag=gr.State(False),
            interaction_phase=gr.State("waiting_for_input")  # New state to track button phase
        )

        with gr.Tabs():
            with gr.Tab("Conversation"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Column(visible=True, elem_classes=["clean-elements"]):
                            buttons = dict(
                                start_new_session=gr.Button("Start New Session...", variant="secondary"),
                                session=[gr.Button(f"History Slot {i+1}", variant="huggingface") for i in range(temporary.MAX_HISTORY_SLOTS)],
                                delete_all_history=gr.Button("Delete All History", variant="primary")
                            )

                    with gr.Column(scale=30, elem_classes=["clean-elements"]):
                        chat_components = dict(
                            session_log=gr.Chatbot(label="Session Log", height=temporary.SESSION_LOG_HEIGHT, elem_classes=["scrollable"], type="messages"),
                            user_input=gr.Textbox(label="User Input", lines=temporary.INPUT_LINES, interactive=False, placeholder="Enter text here...")
                        )
                        with gr.Row(elem_classes=["clean-elements"]):
                            action_buttons = {}
                            with gr.Column(elem_classes=["clean-elements"]):
                                action_buttons.update(
                                    action=gr.Button("Send Input", variant="secondary", scale=20, elem_classes=["send-button"])
                                )
                            with gr.Column(elem_classes=["clean-elements"]):
                                with gr.Row(elem_classes=["clean-elements"]):
                                    action_buttons.update(
                                        edit_previous=gr.Button("Edit Last Input", variant="huggingface"),
                                        copy_response=gr.Button("Copy Last Output", variant="huggingface")
                                    )
                                with gr.Row(elem_classes=["clean-elements"]):
                                    switches = dict(
                                        web_search=gr.Checkbox(label="Web-Search", value=False, visible=True),
                                        tot=gr.Checkbox(label="Enable TOT", value=False, visible=True),
                                        disable_think=gr.Checkbox(label="Disable THINK", value=False, visible=False)
                                    )

                    with gr.Column(scale=1):
                        right_panel = dict(
                            mode_selection=gr.Radio(choices=["Chat", "Code", "Rpg"], label="Select Operation Mode", value="Chat"),
                            toggle_rpg_settings=gr.Button("Show RPG Settings", variant="secondary", elem_classes=["clean-elements"], visible=False),
                            file_attachments=gr.Group(visible=True, elem_classes=["clean-elements"]),
                            rpg_settings=gr.Group(visible=False, elem_classes=["clean-elements"])
                        )
                        with right_panel["file_attachments"]:
                            right_panel.update(
                                attach_files=gr.UploadButton("Attach New Files", file_types=[f".{ext}" for ext in temporary.ALLOWED_EXTENSIONS], file_count="multiple", variant="secondary", elem_classes=["clean-elements"]),
                                file_slots=[gr.Button("File Slot Free", variant="huggingface") for _ in range(temporary.MAX_ATTACH_SLOTS)],
                                remove_all_attachments=gr.Button("Remove All Attachments", variant="primary")
                            )
                        with right_panel["rpg_settings"]:
                            rpg_fields = dict(
                                rp_location=gr.Textbox(label="RP Location", value=temporary.RP_LOCATION),
                                user_name=gr.Textbox(label="User Name", value=temporary.USER_PC_NAME),
                                user_role=gr.Textbox(label="User Role", value=temporary.USER_PC_ROLE),
                                ai_npc=gr.Textbox(label="AI NPC", value=temporary.AI_NPC_NAME),
                                ai_npc_role=gr.Textbox(label="AI Role", value=temporary.AI_NPC_ROLE),
                                save_rpg=gr.Button("Save RPG Settings", variant="primary")
                            )
                with gr.Row():
                    status_text = gr.Textbox(label="Status", interactive=False, value="Select model on Configuration page.", scale=30)
                    gr.Button("Exit Program", variant="stop", elem_classes=["double-height"]).click(fn=shutdown_program, inputs=[states["models_loaded"]])

            with gr.Tab("Configuration"):
                with gr.Column(scale=1, elem_classes=["clean-elements"]):
                    is_cpu_only = temporary.BACKEND_TYPE in ["CPU Only - AVX2", "CPU Only - AVX512", "CPU Only - NoAVX", "CPU Only - OpenBLAS"]
                    config_components = {}
                    with gr.Row(visible=not is_cpu_only, elem_classes=["clean-elements"]):
                        config_components.update(
                            gpu=gr.Dropdown(choices=utility.get_available_gpus(), label="Select GPU", value=temporary.SELECTED_GPU, scale=5),
                            backend_type=gr.Textbox(label="Installed Backend", value=temporary.BACKEND_TYPE, interactive=False, scale=5),
                            vram=gr.Dropdown(choices=temporary.VRAM_OPTIONS, label="Assign Free VRam", value=temporary.VRAM_SIZE, scale=3),
                            mlock_gpu=gr.Checkbox(label="MLock Enabled", value=temporary.MLOCK, scale=3)
                        )
                    with gr.Row(visible=is_cpu_only, elem_classes=["clean-elements"]):
                        cpu_choices = [cpu["label"] for cpu in utility.get_cpu_info()] or ["Default CPU"]
                        config_components.update(
                            backend_type=gr.Textbox(label="Backend Type", value=temporary.BACKEND_TYPE, interactive=False, scale=5),
                            cpu=gr.Dropdown(choices=cpu_choices, label="Select CPU", value=temporary.SELECTED_CPU if temporary.SELECTED_CPU in cpu_choices else cpu_choices[0], scale=5),
                            mlock_cpu=gr.Checkbox(label="MLock Enabled", value=temporary.MLOCK, scale=3)
                        )
                    with gr.Row(elem_classes=["clean-elements"]):
                        config_components.update(
                            model_dir=gr.Textbox(label="Model Folder", value=temporary.MODEL_FOLDER, interactive=False, scale=20),
                            browse=gr.Button("Browse", variant="secondary", elem_classes=["double-height"])
                        )
                    with gr.Row(elem_classes=["clean-elements"]):
                        config_components.update(
                            model=gr.Dropdown(choices=available_models, label="Select Model", value=default_model, allow_custom_value=True, scale=10)
                        )
                        recommended_mode = gr.Textbox(label="Detected Mode Keywords", interactive=False, scale=5)

                    with gr.Row(elem_classes=["clean-elements"]):
                        config_components.update(
                            ctx=gr.Dropdown(choices=temporary.CTX_OPTIONS, label="Context Size", value=temporary.N_CTX),
                            batch=gr.Dropdown(choices=temporary.BATCH_OPTIONS, label="Batch Size", value=temporary.N_BATCH),
                            temp=gr.Dropdown(choices=temporary.TEMP_OPTIONS, label="Temperature", value=temporary.TEMPERATURE),
                            repeat=gr.Dropdown(choices=temporary.REPEAT_OPTIONS, label="Repeat Penalty", value=temporary.REPEAT_PENALTY)
                        )
                        config_components.update(
                            stream_output=gr.Checkbox(label="Stream Output", value=temporary.STREAM_OUTPUT, info="Enable to stream response tokens as they generate.")  # New Stream Output toggle
                        )                    
                    with gr.Row(elem_classes=["clean-elements"]):
                        config_components.update(
                            load_models=gr.Button("Load Model", variant="secondary", elem_classes=["double-height"]),
                            inspect_model=gr.Button("Inspect Model", variant="huggingface", elem_classes=["double-height"]),
                            unload=gr.Button("Unload Model", elem_classes=["double-height"])
                        )
                    custom_components = {}
                    with gr.Row(elem_classes=["clean-elements"]):
                        custom_components.update(
                            max_history_slots=gr.Dropdown(choices=temporary.HISTORY_SLOT_OPTIONS, label="Max History Slots", value=temporary.MAX_HISTORY_SLOTS),
                            session_log_height=gr.Dropdown(choices=temporary.SESSION_LOG_HEIGHT_OPTIONS, label="Session Log Height", value=temporary.SESSION_LOG_HEIGHT),
                            input_lines=gr.Dropdown(choices=temporary.INPUT_LINES_OPTIONS, label="Input Lines", value=temporary.INPUT_LINES),
                            max_attach_slots=gr.Dropdown(choices=temporary.ATTACH_SLOT_OPTIONS, label="Max Attach Slots", value=temporary.MAX_ATTACH_SLOTS)
                        )
                        custom_components.update(
                            afterthought_time=gr.Checkbox(label="After-Thought Time", value=temporary.AFTERTHOUGHT_TIME)
                        )                            
                    with gr.Row(elem_classes=["clean-elements"]):
                        config_components.update(
                            save_settings=gr.Button("Save Settings", variant="primary", elem_classes=["double-height"])
                        )
                        custom_components.update(
                            delete_all_vectorstores=gr.Button("Delete All VectorStores", variant="stop", elem_classes=["double-height"])
                        )
                    with gr.Row(elem_classes=["clean-elements"]):
                        gr.Markdown("Notes: Changes to Max History Slots and Max Attach Slots require restarting the application.")
                    with gr.Row(elem_classes=["clean-elements"]):
                        config_components.update(
                            status_settings=gr.Textbox(label="Status", interactive=False, scale=20),
                            shutdown=gr.Button("Exit Program", variant="stop", elem_classes=["double-height"]).click(fn=shutdown_program, inputs=[states["models_loaded"]])
                        )

        # Helper Functions
        def select_model_folder():
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            initial_dir = temporary.MODEL_FOLDER if os.path.exists(temporary.MODEL_FOLDER) else os.path.expanduser("~")
            folder = filedialog.askdirectory(initialdir=initial_dir, title="Select Model Folder")
            root.destroy()
            temporary.MODEL_FOLDER = folder or temporary.MODEL_FOLDER
            return temporary.MODEL_FOLDER

        def update_model_list(folder):
            temporary.MODEL_FOLDER = folder
            models_list = models.get_available_models() or ["No models found"]
            value = temporary.MODEL_NAME if temporary.MODEL_NAME in models_list else models_list[0]
            return gr.update(choices=models_list, value=value)

        def update_config_settings(*args):
            keys = ["ctx", "batch", "temp", "repeat", "vram", "gpu", "cpu", "model", "model_dir"]
            attr_map = {
                "ctx": "N_CTX", "batch": "N_BATCH", "temp": "TEMPERATURE", "repeat": "REPEAT_PENALTY",
                "vram": "VRAM_SIZE", "gpu": "SELECTED_GPU", "cpu": "SELECTED_CPU", "model": "MODEL_NAME",
                "model_dir": "MODEL_FOLDER"
            }
            for k, v in zip(keys, args):
                if k in attr_map:
                    setattr(temporary, attr_map[k], int(v) if k in ["ctx", "batch", "vram"] else float(v) if k in ["temp", "repeat"] else v)
            return "Settings updated in memory. Click 'Save Settings' to commit."

        def update_mlock(mlock):
            temporary.MLOCK = mlock
            return "MLock updated."

        def update_stream_output(value):
            temporary.STREAM_OUTPUT = value
            return f"Stream Output {'enabled' if value else 'disabled'}."

        def save_all_settings():
            utility.save_config()
            return "Settings saved to persistent.json"

        async def action_handler(phase, user_input, session_log, tot_enabled, loaded_files, disable_think,
                                 rp_location, user_name, user_role, ai_npc, cancel_flag, mode_selection,
                                 web_search_enabled, models_loaded, interaction_phase):
            if phase == "waiting_for_input":
                async for output in chat_interface(user_input, session_log, tot_enabled, loaded_files, disable_think,
                                                   rp_location, user_name, user_role, ai_npc, cancel_flag, mode_selection,
                                                   web_search_enabled, models_loaded, interaction_phase):
                    yield output
            else:
                if phase == "afterthought_countdown":
                    cancel_flag = True
                    new_phase = "waiting_for_input"
                    status_msg = "Input cancelled."
                elif phase == "generating_response":
                    cancel_flag = True
                    new_phase = "waiting_for_input"
                    status_msg = "Response generation cancelled."
                else:
                    new_phase = interaction_phase
                    status_msg = "No action taken."
                yield session_log, status_msg, update_action_button(new_phase), cancel_flag, loaded_files, new_phase

        def send_input(user_input, session_log, tot_enabled, loaded_files_state, disable_think,
                       rp_location, user_name, user_role, ai_npc, cancel_flag, mode_selection,
                       web_search_enabled, models_loaded, interaction_phase):
            """Handle the Send Response action."""
            return chat_interface(user_input, session_log, tot_enabled, loaded_files_state, disable_think,
                                  rp_location, user_name, user_role, ai_npc, cancel_flag, mode_selection,
                                  web_search_enabled, models_loaded, interaction_phase)

        def cancel_action(cancel_flag, interaction_phase):
            """Handle cancellation based on current phase."""
            if interaction_phase == "afterthought_countdown":
                return True, "waiting_for_input", "Input cancelled."
            elif interaction_phase == "generating_response":
                return True, "waiting_for_input", "Response generation cancelled."
            return cancel_flag, interaction_phase, "No action taken."

        # Event Handlers
        buttons["start_new_session"].click(
            fn=start_new_session,
            outputs=[chat_components["session_log"], status_text, chat_components["user_input"]]
        )

        action_buttons["action"].click(
            fn=action_handler,
            inputs=[
                states["interaction_phase"],
                chat_components["user_input"],
                chat_components["session_log"],
                switches["tot"],
                states["loaded_files"],
                switches["disable_think"],
                rpg_fields["rp_location"],
                rpg_fields["user_name"],
                rpg_fields["user_role"],
                rpg_fields["ai_npc"],
                states["cancel_flag"],
                right_panel["mode_selection"],
                switches["web_search"],
                states["models_loaded"],
                states["interaction_phase"]
            ],
            outputs=[
                chat_components["session_log"],
                status_text,
                action_buttons["action"],
                states["cancel_flag"],
                states["loaded_files"],
                states["interaction_phase"]
            ]
        )

        action_buttons["copy_response"].click(
            fn=copy_last_response,
            inputs=[chat_components["session_log"]],
            outputs=[status_text]
        )
        right_panel["attach_files"].upload(
            fn=process_uploaded_files,
            inputs=[right_panel["attach_files"], states["loaded_files"], states["models_loaded"]],
            outputs=[status_text, states["loaded_files"]]
        )
        right_panel["remove_all_attachments"].click(
            fn=remove_all_attachments,
            inputs=[states["loaded_files"]],
            outputs=[states["loaded_files"], status_text] + right_panel["file_slots"] + [right_panel["attach_files"]]
        )
        for i, btn in enumerate(right_panel["file_slots"]):
            btn.click(
                fn=eject_file,
                inputs=[states["loaded_files"], gr.State(value=i)],
                outputs=[states["loaded_files"], status_text] + right_panel["file_slots"] + [right_panel["attach_files"]]
            )
        for comp in [config_components[k] for k in ["ctx", "batch", "temp", "repeat", "vram", "gpu", "cpu", "model"]]:
            comp.change(
                fn=update_config_settings,
                inputs=[config_components[k] for k in ["ctx", "batch", "temp", "repeat", "vram", "gpu", "cpu", "model"]] + [config_components["model_dir"]],
                outputs=[config_components["status_settings"]]
            )
        config_components["browse"].click(
            fn=select_model_folder,
            outputs=[config_components["model_dir"]]
        ).then(
            fn=update_model_list,
            inputs=[config_components["model_dir"]],
            outputs=[config_components["model"]]
        ).then(
            fn=lambda f: f"Model directory updated to: {f}",
            inputs=[config_components["model_dir"]],
            outputs=[config_components["status_settings"]]
        )
        for chk in [config_components.get(k) for k in ["mlock_gpu", "mlock_cpu"] if config_components.get(k)]:
            chk.change(
                fn=update_mlock,
                inputs=[chk],
                outputs=[config_components["status_settings"]]
            )
        config_components["stream_output"].change(  # Event handler for Stream Output toggle
            fn=update_stream_output,
            inputs=[config_components["stream_output"]],
            outputs=[config_components["status_settings"]]
        )
        config_components["unload"].click(
            fn=models.unload_models,
            outputs=[config_components["status_settings"]]
        ).then(
            fn=lambda: False,
            outputs=[states["models_loaded"]]
        ).then(
            fn=lambda: gr.update(interactive=False),
            outputs=[chat_components["user_input"]]
        )
        config_components["inspect_model"].click(
            fn=models.inspect_model,
            inputs=[config_components["model"], config_components["vram"]],
            outputs=[config_components["status_settings"]]
        )
        config_components["load_models"].click(
            fn=set_loading_status,
            outputs=[config_components["status_settings"]]
        ).then(
            fn=models.load_models,
            inputs=[config_components["model"], config_components["vram"]],
            outputs=[config_components["status_settings"], states["models_loaded"]]
        ).then(
            fn=lambda ml: gr.update(interactive=ml),
            inputs=[states["models_loaded"]],
            outputs=[chat_components["user_input"]]
        )
        config_components["save_settings"].click(
            fn=save_all_settings,
            outputs=[config_components["status_settings"]]
        )
        buttons["delete_all_history"].click(
            fn=lambda: ("All history deleted.", *[gr.update() for _ in buttons["session"]]),
            outputs=[status_text] + buttons["session"]
        )
        right_panel["toggle_rpg_settings"].click(
            fn=toggle_rpg_settings,
            inputs=[states["showing_rpg_right"]],
            outputs=[right_panel["toggle_rpg_settings"], right_panel["file_attachments"], right_panel["rpg_settings"], states["showing_rpg_right"]]
        )
        rpg_fields["save_rpg"].click(
            fn=save_rp_settings,
            inputs=list(rpg_fields.values())[:-1],
            outputs=list(rpg_fields.values())[:-1]
        )
        custom_components["delete_all_vectorstores"].click(
            fn=utility.delete_all_session_vectorstores,
            outputs=[config_components["status_settings"]]
        )
        custom_components["session_log_height"].change(
            fn=lambda h: gr.update(height=h),
            inputs=[custom_components["session_log_height"]],
            outputs=[chat_components["session_log"]]
        )
        custom_components["input_lines"].change(
            fn=lambda l: gr.update(lines=l),
            inputs=[custom_components["input_lines"]],
            outputs=[chat_components["user_input"]]
        )
        custom_components["max_history_slots"].change(
            fn=lambda s: setattr(temporary, "MAX_HISTORY_SLOTS", s) or None,
            inputs=[custom_components["max_history_slots"]]
        ).then(
            fn=update_session_buttons,
            outputs=buttons["session"]
        )
        custom_components["max_attach_slots"].change(
            fn=lambda s: setattr(temporary, "MAX_ATTACH_SLOTS", s) or None,
            inputs=[custom_components["max_attach_slots"]]
        ).then(
            fn=update_file_slot_ui,
            inputs=[states["loaded_files"]],
            outputs=right_panel["file_slots"] + [right_panel["attach_files"]]
        )
        custom_components["afterthought_time"].change(
            fn=lambda v: setattr(temporary, "AFTERTHOUGHT_TIME", v),
            inputs=[custom_components["afterthought_time"]],
            outputs=[config_components["status_settings"]]
        )
        config_components["model"].change(
            fn=update_model_based_options,
            inputs=[config_components["model"]],
            outputs=[right_panel["mode_selection"], switches["disable_think"], recommended_mode]
        ).then(
            fn=update_mode_based_options,
            inputs=[right_panel["mode_selection"], states["showing_rpg_right"]],
            outputs=[switches["tot"], switches["web_search"], right_panel["attach_files"], right_panel["toggle_rpg_settings"], right_panel["file_attachments"], right_panel["rpg_settings"], states["showing_rpg_right"]]
        )
        right_panel["mode_selection"].change(
            fn=update_mode_based_options,
            inputs=[right_panel["mode_selection"], states["showing_rpg_right"]],
            outputs=[switches["tot"], switches["web_search"], right_panel["attach_files"], right_panel["toggle_rpg_settings"], right_panel["file_attachments"], right_panel["rpg_settings"], states["showing_rpg_right"]]
        )

        demo.launch(server_name="127.0.0.1", server_port=7860, show_error=True, show_api=False)


if __name__ == "__main__":
    launch_interface()