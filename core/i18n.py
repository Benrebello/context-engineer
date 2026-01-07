"""Internationalization (i18n) system for Context Engineer CLI.

Provides bilingual support (EN-US/PT-BR) with automatic language detection
from project configuration.

IMPORTANT: CLI commands, flags, and aliases are ALWAYS in English (industry standard).
Only descriptions, messages, and prompts are translated.

Examples:
  ✅ CORRECT:
    Command: ce init (always English)
    Description: "Initialize project" / "Inicializar projeto" (translated)
  
  ❌ WRONG:
    Command: ce iniciar (never translate commands)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Default language
DEFAULT_LANGUAGE = "en-us"

# NOTE: CLI commands are NEVER translated
# Commands like 'ce init', 'ce generate-prd', flags like '--stack', '--output'
# and aliases like 'gp', 'gpr' are ALWAYS in English (industry standard)
# Only descriptions, messages, and user-facing text are translated

# Translation dictionary
TRANSLATIONS = {
    "en-us": {
        # Common messages
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "info": "Info",
        "tip": "Tip",
        "example": "Example",
        "next_step": "Next step",
        "prerequisites": "Prerequisites",
        "not_found": "not found",
        "completed": "completed",
        "failed": "failed",
        
        # Commands
        "cmd.init.success": "Project {name} initialized at {path}",
        "cmd.init.stack": "Stack: {stack}",
        "cmd.init.tip_alias": "Use 'ce gp' as shortcut for 'ce generate-prd'",
        "cmd.init.git_not_found": "Directory .git not found. Git hooks were not generated.",
        "cmd.init.git_tip": "Run 'git init' first or pass --no-git-hooks to skip.",
        "cmd.init.git_later": "Or install hooks later via: ce install-hooks",
        
        "cmd.generate_prd.success": "PRD generated at {path}",
        "cmd.generate_prd.next_step": "Next step: Execute 'ce generate-prps' or 'ce gpr'",
        "cmd.generate_prd.validated": "PRD validated successfully",
        "cmd.generate_prd.missing_fields": "Missing fields: {fields}",
        "cmd.generate_prd.validation_error": "Validation error: {error}",
        
        "cmd.generate_prps.prereq_failed": "Prerequisite not met: PRD not found. Execute 'ce generate-prd' first.",
        "cmd.generate_prps.tip": "Execute 'ce generate-prd' first or use 'ce gpr --interactive'",
        "cmd.generate_prps.prd_detected": "PRD detected at: {path}",
        "cmd.generate_prps.prd_not_found": "PRD not found automatically.",
        "cmd.generate_prps.prd_not_found_error": "PRD not found. Use --interactive for guided mode or pass the PRD file path.",
        
        "cmd.generate_tasks.prereq_failed": "Prerequisite not met: PRPs not found. Execute 'ce generate-prps' first.",
        
        "cmd.validate.prereq_failed": "Prerequisite not met: PRD not found. Nothing to validate.",
        "cmd.validate.tip": "Execute commands in the correct pipeline order",
        
        # Errors
        "error.file_not_found": "File not found: {file}",
        "error.file_not_found_tip": "Check if the path is correct",
        "error.permission_denied": "Permission denied: {file}",
        "error.permission_denied_tip": "Execute with appropriate permissions or check file owner",
        "error.unexpected": "Unexpected error: {error}",
        "error.unexpected_tip": "Execute 'ce doctor' for complete diagnostics",
        "error.prereq_validation_failed": "Could not validate prerequisites: {error}",
        
        # Quickstart
        "quickstart.title": "CONTEXT ENGINEER - QUICKSTART",
        "quickstart.welcome": "Welcome! This guide will set up your first project in 5 minutes.",
        "quickstart.what_we_do": "What we'll do:",
        "quickstart.step1": "Create project structure",
        "quickstart.step2": "Generate PRD (Product Requirements Document)",
        "quickstart.step3": "Generate PRPs (Phase Requirement Plans)",
        "quickstart.step4": "View project status",
        "quickstart.interrupt": "You can interrupt at any time with Ctrl+C",
        "quickstart.ready": "Ready to start?",
        "quickstart.cancelled": "Quickstart cancelled. Execute 'ce quickstart' when ready.",
        "quickstart.step_init": "Initialize Project",
        "quickstart.step_prd": "Generate PRD",
        "quickstart.step_prps": "Generate PRPs",
        "quickstart.step_status": "Project Status",
        "quickstart.project_name": "Project name",
        "quickstart.choose_stack": "Choose the stack",
        "quickstart.available_stacks": "Available stacks:",
        "quickstart.initializing": "Initializing project '{name}' with stack '{stack}'...",
        "quickstart.init_success": "Project initialized!",
        "quickstart.create_prd_now": "Do you want to create the PRD now?",
        "quickstart.prd_later": "You can generate the PRD later with: ce generate-prd --interactive",
        "quickstart.prd_simple": "Let's create a simple PRD. Answer a few questions:",
        "quickstart.prd_success": "PRD created!",
        "quickstart.generate_prps_now": "Do you want to generate PRPs now?",
        "quickstart.prps_later": "You can generate PRPs later with: ce generate-prps",
        "quickstart.generating_prps": "Generating PRPs (this may take a few seconds)...",
        "quickstart.prps_success": "PRPs generated!",
        "quickstart.completed": "QUICKSTART COMPLETED!",
        "quickstart.interrupted": "Quickstart interrupted. You can resume by executing 'ce quickstart'",
        "quickstart.next_steps": "Recommended Next Steps:",
        "quickstart.next_step_tasks": "Generate executable tasks:",
        "quickstart.next_step_validate": "Validate traceability:",
        "quickstart.next_step_checklist": "View interactive checklist:",
        "quickstart.next_step_assist": "Use conversational assistant:",
        "quickstart.tips": "Tips:",
        "quickstart.tip_aliases": "Use aliases for quick commands: ce gp, ce gpr, ce gt",
        "quickstart.tip_help": "Execute 'ce --help' to see all commands",
        "quickstart.tip_status": "Execute 'ce status' anytime to see progress",
        
        # Explore
        "explore.title": "COMMAND EXPLORER - CONTEXT ENGINEER",
        "explore.category_not_found": "Category '{category}' not found",
        "explore.available_categories": "Available categories:",
        "explore.tips": "Tips:",
        "explore.tip_help": "Use 'ce <command> --help' to see details of each command",
        "explore.tip_filter": "Use 'ce explore --category generation' to filter by category",
        "explore.tip_quickstart": "Execute 'ce quickstart' to start quickly",
        
        "explore.cat_generation": "Generation",
        "explore.cat_generation_desc": "Commands to generate project artifacts",
        "explore.cat_validation": "Validation",
        "explore.cat_validation_desc": "Commands to validate quality and traceability",
        "explore.cat_reports": "Reports",
        "explore.cat_reports_desc": "Commands to view metrics and status",
        "explore.cat_automation": "Automation",
        "explore.cat_automation_desc": "Commands for automation and assistance",
        "explore.cat_devops": "DevOps",
        "explore.cat_devops_desc": "Commands for CI/CD and Git",
        "explore.cat_extensions": "Extensions",
        "explore.cat_extensions_desc": "Commands for patterns and marketplace",
        "explore.cat_config": "Configuration",
        "explore.cat_config_desc": "Commands for configuration and governance",
        
        # Prompts
        "prompt.multiline_title": "How to finish:",
        "prompt.multiline_enter": "Press Enter twice (empty line)",
        "prompt.multiline_ctrl_d": "Or press Ctrl+D",
        
        # Assist
        "assist.warning_open_html": "--open is only supported when --format=html. Flag ignored.",
        "assist.report_saved": "HTML report saved at {path}",
        "assist.browser_error": "Could not open browser automatically: {error}",
        "assist.lets_init": "Let's start by initializing the project.",
        "assist.run_init": "Do you want to run 'ce init' now?",
        "assist.init_success": "Project initialized successfully!",
        "assist.next_prd": "Next step: create the PRD (Product Requirements Document).",
        "assist.generate_prd": "Generate the PRD now?",
        "assist.prd_success": "PRD created successfully!",
        "assist.next_prps": "Now, let's generate PRPs (Phase Requirement Plans).",
        "assist.generate_prps": "Generate PRPs now?",
        "assist.prps_success": "PRPs generated successfully!",
        "assist.next_tasks": "Time to generate executable Tasks from the PRPs.",
        "assist.generate_tasks": "Generate Tasks now?",
        "assist.tasks_success": "Tasks generated successfully!",
        "assist.process_completed": "Guided process completed!",
        "assist.recommended_next": "Recommended next steps:",
        "assist.review_files": "Review the generated files",
        "assist.run_validate": "Run 'ce validate' to check traceability",
        "assist.run_status": "Run 'ce status' to inspect overall progress",
        "assist.start_tasks": "Start implementing Tasks via the IDE agents",
        "assist.interrupted": "Assistant interrupted.",
    },
    "pt-br": {
        # Common messages
        "success": "Sucesso",
        "error": "Erro",
        "warning": "Aviso",
        "info": "Info",
        "tip": "Dica",
        "example": "Exemplo",
        "next_step": "Próximo passo",
        "prerequisites": "Pré-requisitos",
        "not_found": "não encontrado",
        "completed": "concluído",
        "failed": "falhou",
        
        # Commands
        "cmd.init.success": "Projeto {name} inicializado em {path}",
        "cmd.init.stack": "Stack: {stack}",
        "cmd.init.tip_alias": "Use 'ce gp' como atalho para 'ce generate-prd'",
        "cmd.init.git_not_found": "Diretório .git não encontrado. Git hooks não foram gerados.",
        "cmd.init.git_tip": "Execute 'git init' primeiro ou use --no-git-hooks para pular.",
        "cmd.init.git_later": "Ou instale hooks depois via: ce install-hooks",
        
        "cmd.generate_prd.success": "PRD gerado em {path}",
        "cmd.generate_prd.next_step": "Próximo passo: Execute 'ce generate-prps' ou 'ce gpr'",
        "cmd.generate_prd.validated": "PRD validado com sucesso",
        "cmd.generate_prd.missing_fields": "Campos faltando: {fields}",
        "cmd.generate_prd.validation_error": "Erro de validação: {error}",
        
        "cmd.generate_prps.prereq_failed": "Pré-requisito não atendido: PRD não encontrado. Execute 'ce generate-prd' primeiro.",
        "cmd.generate_prps.tip": "Execute 'ce generate-prd' primeiro ou use 'ce gpr --interactive'",
        "cmd.generate_prps.prd_detected": "PRD detectado em: {path}",
        "cmd.generate_prps.prd_not_found": "PRD não encontrado automaticamente.",
        "cmd.generate_prps.prd_not_found_error": "PRD não encontrado. Use --interactive para modo guiado ou passe o caminho do arquivo PRD.",
        
        "cmd.generate_tasks.prereq_failed": "Pré-requisito não atendido: PRPs não encontrados. Execute 'ce generate-prps' primeiro.",
        
        "cmd.validate.prereq_failed": "Pré-requisito não atendido: PRD não encontrado. Não há nada para validar.",
        "cmd.validate.tip": "Execute os comandos na ordem correta do pipeline",
        
        # Errors
        "error.file_not_found": "Arquivo não encontrado: {file}",
        "error.file_not_found_tip": "Verifique se o caminho está correto",
        "error.permission_denied": "Permissão negada: {file}",
        "error.permission_denied_tip": "Execute com permissões adequadas ou verifique o proprietário do arquivo",
        "error.unexpected": "Erro inesperado: {error}",
        "error.unexpected_tip": "Execute 'ce doctor' para diagnóstico completo",
        "error.prereq_validation_failed": "Não foi possível validar pré-requisitos: {error}",
        
        # Quickstart
        "quickstart.title": "CONTEXT ENGINEER - INÍCIO RÁPIDO",
        "quickstart.welcome": "Bem-vindo! Este guia vai configurar seu primeiro projeto em 5 minutos.",
        "quickstart.what_we_do": "O que vamos fazer:",
        "quickstart.step1": "Criar estrutura do projeto",
        "quickstart.step2": "Gerar PRD (Product Requirements Document)",
        "quickstart.step3": "Gerar PRPs (Phase Requirement Plans)",
        "quickstart.step4": "Visualizar status do projeto",
        "quickstart.interrupt": "Você pode interromper a qualquer momento com Ctrl+C",
        "quickstart.ready": "Pronto para começar?",
        "quickstart.cancelled": "Início rápido cancelado. Execute 'ce quickstart' quando estiver pronto.",
        "quickstart.step_init": "Inicializar Projeto",
        "quickstart.step_prd": "Gerar PRD",
        "quickstart.step_prps": "Gerar PRPs",
        "quickstart.step_status": "Status do Projeto",
        "quickstart.project_name": "Nome do projeto",
        "quickstart.choose_stack": "Escolha a stack",
        "quickstart.available_stacks": "Stacks disponíveis:",
        "quickstart.initializing": "Inicializando projeto '{name}' com stack '{stack}'...",
        "quickstart.init_success": "Projeto inicializado!",
        "quickstart.create_prd_now": "Deseja criar o PRD agora?",
        "quickstart.prd_later": "Você pode gerar o PRD depois com: ce generate-prd --interactive",
        "quickstart.prd_simple": "Vamos criar um PRD simples. Responda algumas perguntas:",
        "quickstart.prd_success": "PRD criado!",
        "quickstart.generate_prps_now": "Deseja gerar os PRPs agora?",
        "quickstart.prps_later": "Você pode gerar os PRPs depois com: ce generate-prps",
        "quickstart.generating_prps": "Gerando PRPs (isso pode levar alguns segundos)...",
        "quickstart.prps_success": "PRPs gerados!",
        "quickstart.completed": "INÍCIO RÁPIDO CONCLUÍDO!",
        "quickstart.interrupted": "Início rápido interrompido. Você pode retomar executando 'ce quickstart'",
        "quickstart.next_steps": "Próximos Passos Recomendados:",
        "quickstart.next_step_tasks": "Gerar tasks executáveis:",
        "quickstart.next_step_validate": "Validar rastreabilidade:",
        "quickstart.next_step_checklist": "Ver checklist interativo:",
        "quickstart.next_step_assist": "Usar assistente conversacional:",
        "quickstart.tips": "Dicas:",
        "quickstart.tip_aliases": "Use aliases para comandos rápidos: ce gp, ce gpr, ce gt",
        "quickstart.tip_help": "Execute 'ce --help' para ver todos os comandos",
        "quickstart.tip_status": "Execute 'ce status' a qualquer momento para ver o progresso",
        
        # Explore
        "explore.title": "EXPLORADOR DE COMANDOS - CONTEXT ENGINEER",
        "explore.category_not_found": "Categoria '{category}' não encontrada",
        "explore.available_categories": "Categorias disponíveis:",
        "explore.tips": "Dicas:",
        "explore.tip_help": "Use 'ce <comando> --help' para ver detalhes de cada comando",
        "explore.tip_filter": "Use 'ce explore --category geração' para filtrar por categoria",
        "explore.tip_quickstart": "Execute 'ce quickstart' para começar rapidamente",
        
        "explore.cat_generation": "Geração",
        "explore.cat_generation_desc": "Comandos para gerar artefatos do projeto",
        "explore.cat_validation": "Validação",
        "explore.cat_validation_desc": "Comandos para validar qualidade e rastreabilidade",
        "explore.cat_reports": "Relatórios",
        "explore.cat_reports_desc": "Comandos para visualizar métricas e status",
        "explore.cat_automation": "Automação",
        "explore.cat_automation_desc": "Comandos para automação e assistência",
        "explore.cat_devops": "DevOps",
        "explore.cat_devops_desc": "Comandos para CI/CD e Git",
        "explore.cat_extensions": "Extensões",
        "explore.cat_extensions_desc": "Comandos para padrões e marketplace",
        "explore.cat_config": "Configuração",
        "explore.cat_config_desc": "Comandos para configuração e governança",
        
        # Prompts
        "prompt.multiline_title": "Como finalizar:",
        "prompt.multiline_enter": "Pressione Enter duas vezes (linha vazia)",
        "prompt.multiline_ctrl_d": "Ou pressione Ctrl+D",
        
        # Assist
        "assist.warning_open_html": "--open é suportado apenas quando --format=html. Flag ignorada.",
        "assist.report_saved": "Relatório HTML salvo em {path}",
        "assist.browser_error": "Não foi possível abrir o navegador automaticamente: {error}",
        "assist.lets_init": "Vamos começar inicializando o projeto.",
        "assist.run_init": "Deseja executar 'ce init' agora?",
        "assist.init_success": "Projeto inicializado com sucesso!",
        "assist.next_prd": "Próximo passo: criar o PRD (Product Requirements Document).",
        "assist.generate_prd": "Gerar o PRD agora?",
        "assist.prd_success": "PRD criado com sucesso!",
        "assist.next_prps": "Agora, vamos gerar os PRPs (Phase Requirement Plans).",
        "assist.generate_prps": "Gerar PRPs agora?",
        "assist.prps_success": "PRPs gerados com sucesso!",
        "assist.next_tasks": "Hora de gerar Tasks executáveis a partir dos PRPs.",
        "assist.generate_tasks": "Gerar Tasks agora?",
        "assist.tasks_success": "Tasks geradas com sucesso!",
        "assist.process_completed": "Processo guiado concluído!",
        "assist.recommended_next": "Próximos passos recomendados:",
        "assist.review_files": "Revisar os arquivos gerados",
        "assist.run_validate": "Executar 'ce validate' para verificar rastreabilidade",
        "assist.run_status": "Executar 'ce status' para inspecionar progresso geral",
        "assist.start_tasks": "Começar a implementar Tasks via agentes IDE",
        "assist.interrupted": "Assistente interrompido.",
    }
}


class I18n:
    """Internationalization manager for Context Engineer."""
    
    def __init__(self, language: str | None = None, project_dir: Path | None = None):
        """Initialize i18n with language preference.
        
        Args:
            language: Language code (en-us or pt-br). If None, tries to load from project config.
            project_dir: Project directory to load config from.
        """
        self.language = self._resolve_language(language, project_dir)
    
    def _resolve_language(self, language: str | None, project_dir: Path | None) -> str:
        """Resolve language from parameter, config, or default."""
        # 1. Explicit parameter
        if language:
            return self._normalize_language(language)
        
        # 2. Project configuration
        if project_dir:
            config_path = project_dir / ".ce-config.json"
            if config_path.exists():
                try:
                    with open(config_path, encoding="utf-8") as f:
                        config = json.load(f)
                        if "language" in config:
                            return self._normalize_language(config["language"])
                except Exception:
                    pass
        
        # 3. Default
        return DEFAULT_LANGUAGE
    
    def _normalize_language(self, lang: str) -> str:
        """Normalize language code."""
        lang_lower = lang.lower().strip()
        
        # Map common variations
        lang_map = {
            "en": "en-us",
            "en-us": "en-us",
            "english": "en-us",
            "pt": "pt-br",
            "pt-br": "pt-br",
            "portuguese": "pt-br",
            "portugues": "pt-br",
            "português": "pt-br",
        }
        
        return lang_map.get(lang_lower, DEFAULT_LANGUAGE)
    
    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key with optional formatting parameters.
        
        Args:
            key: Translation key (e.g., 'cmd.init.success')
            **kwargs: Format parameters for the translation string
            
        Returns:
            Translated and formatted string
        """
        translations = TRANSLATIONS.get(self.language, TRANSLATIONS[DEFAULT_LANGUAGE])
        template = translations.get(key, key)
        
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        
        return template
    
    def set_language(self, language: str) -> None:
        """Change the current language."""
        self.language = self._normalize_language(language)


# Global instance (will be initialized per command)
_i18n_instance: I18n | None = None


def get_i18n(language: str | None = None, project_dir: Path | None = None) -> I18n:
    """Get or create i18n instance.
    
    Args:
        language: Language code
        project_dir: Project directory
        
    Returns:
        I18n instance
    """
    global _i18n_instance
    
    # Always create new instance if parameters provided
    if language is not None or project_dir is not None:
        return I18n(language=language, project_dir=project_dir)
    
    # Return cached instance or create default
    if _i18n_instance is None:
        _i18n_instance = I18n()
    
    return _i18n_instance


def t(key: str, **kwargs: Any) -> str:
    """Shorthand for translation.
    
    Args:
        key: Translation key
        **kwargs: Format parameters
        
    Returns:
        Translated string
    """
    return get_i18n().t(key, **kwargs)


__all__ = ["I18n", "get_i18n", "t", "DEFAULT_LANGUAGE", "TRANSLATIONS"]
