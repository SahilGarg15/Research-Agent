"""
Auto-Research Agent 2.0 - Streamlit Web Application
Modern web interface for the research platform.
"""

import streamlit as st
import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import authentication
from auth.authentication import UserDatabase, UsageTracker, JWTManager, AuthenticationError
from auth.password_recovery import PasswordRecovery

# Import research components
from research.research_modes import ResearchModeManager, ResearchMode
from research.query_processor import QueryProcessor
from utils.search_engines import MultiSourceSearchEngine

# Import utilities
from utils.cache_system import get_cache
from utils.advanced_exports import get_exporter
from utils.chart_generator import get_chart_generator
from utils.credibility_scorer import get_credibility_scorer

# Import orchestrator
from orchestrator.tiered_workflow import TieredResearchOrchestrator
from models.router import ModelRouter

# Page configuration
st.set_page_config(
    page_title="Auto-Research Agent 2.0",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #1e1e1e;
    }
    .stButton>button {
        background-color: #007acc;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #005a9e;
    }
    .success-box {
        padding: 15px;
        background-color: #a6e3a1;
        color: #000;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        padding: 15px;
        background-color: #f38ba8;
        color: #000;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        padding: 15px;
        background-color: #89b4fa;
        color: #000;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


class AutoResearchApp:
    """Main Streamlit application."""
    
    def __init__(self):
        """Initialize the application."""
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.tier = None
        
        # Initialize services
        self.db = UserDatabase()
        self.usage_tracker = UsageTracker()
        self.jwt_manager = JWTManager()
        self.password_recovery = PasswordRecovery(self.db)
        
        # Initialize research components
        self.mode_manager = ResearchModeManager()
        self.query_processor = QueryProcessor()
        self.search_engine = MultiSourceSearchEngine()
        
        # Initialize utilities
        self.cache = get_cache(similarity_enabled=True)
        self.exporter = get_exporter()
        self.chart_generator = get_chart_generator()
        self.credibility_scorer = get_credibility_scorer()
        
        # Initialize model router
        self.model_router = ModelRouter()
    
    def show_login_page(self):
        """Show login/signup page."""
        st.title("🔬 Auto-Research Agent 2.0")
        st.markdown("### Advanced AI-Powered Research Platform")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            self._show_login_form()
        
        with tab2:
            self._show_signup_form()
    
    def _show_login_form(self):
        """Show login form."""
        st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    try:
                        user = self.db.verify_user(username, password)
                        if not user:
                            st.error("Invalid username or password")
                            return
                        st.session_state.authenticated = True
                        st.session_state.user_id = user['id']
                        st.session_state.username = user['username']
                        st.session_state.tier = user.get('tier', 'free')
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()
                    except AuthenticationError as e:
                        st.error(str(e))
    
    def _show_signup_form(self):
        """Show signup form."""
        st.subheader("Create Account")
        
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not all([name, email, username, password, confirm_password]):
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    try:
                        user_id = self.db.create_user(name, email, username, password)
                        st.success("Account created successfully! Please login.")
                    except Exception as e:
                        st.error(f"Failed to create account: {str(e)}")
    
    def show_dashboard(self):
        """Show main dashboard."""
        # Sidebar
        with st.sidebar:
            st.title("🔬 Research Agent")
            st.markdown(f"**User:** {st.session_state.username}")
            st.markdown(f"**Tier:** {st.session_state.tier.upper()}")
            st.markdown("---")
            
            # Usage stats
            usage_count = self.usage_tracker.get_usage_today(st.session_state.user_id)
            limit = "Unlimited" if st.session_state.tier == "premium" else "5"
            st.metric("Daily Usage", f"{usage_count} / {limit}")
            
            # Cache stats
            cache_stats = self.cache.get_stats()
            st.metric("Cache Entries", cache_stats['total_entries'])
            
            st.markdown("---")
            
            # Navigation
            page = st.radio(
                "Navigation",
                ["🔬 New Research", "📚 History", "📊 Statistics", "⚙️ Settings"],
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.tier = None
                st.rerun()
        
        # Main content
        if page == "🔬 New Research":
            self._show_research_page()
        elif page == "📚 History":
            self._show_history_page()
        elif page == "📊 Statistics":
            self._show_statistics_page()
        elif page == "⚙️ Settings":
            self._show_settings_page()
    
    def _show_research_page(self):
        """Show research interface."""
        st.title("🔬 New Research")
        
        # Check usage limit
        can_search, message = self.usage_tracker.can_search(st.session_state.user_id, st.session_state.tier)
        if not can_search:
            st.error(f"⚠️ {message}")
            return
        
        # Research mode selection
        st.subheader("Select Research Mode")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⚡ Quick", use_container_width=True, help="Fast overview • 2 sources • ~500 words"):
                st.session_state.selected_mode = "quick"
        
        with col2:
            if st.button("📝 Standard", use_container_width=True, help="Balanced research • 5 sources • ~2000 words"):
                st.session_state.selected_mode = "standard"
        
        with col3:
            disabled = st.session_state.tier != "premium"
            if st.button("🔍 Deep", use_container_width=True, help="Comprehensive • 15+ sources • 5000+ words • Premium only", disabled=disabled):
                st.session_state.selected_mode = "deep"
        
        # Display selected mode
        if 'selected_mode' in st.session_state:
            mode = st.session_state.selected_mode
            from research.research_modes import ResearchMode
            mode_enum = ResearchMode(mode)
            mode_config = self.mode_manager.get_config(mode_enum)
            
            st.info(f"**Selected Mode:** {mode.capitalize()} - {mode_config.max_sources} sources, ~{mode_config.max_words} words")
        
        # Query input
        st.subheader("Enter Research Query")
        query = st.text_area("What would you like to research?", height=100, placeholder="e.g., Impact of artificial intelligence in healthcare")
        
        # Start research button
        if st.button("🚀 Start Research", use_container_width=True, type="primary"):
            if not query:
                st.error("Please enter a research query")
            elif 'selected_mode' not in st.session_state:
                st.error("Please select a research mode")
            else:
                self._run_research(query, st.session_state.selected_mode)
    
    def _run_research(self, query: str, mode: str):
        """Execute research workflow."""
        with st.spinner("🔍 Researching..."):
            try:
                # Process query
                st.info(f"📝 Processing query: {query}")
                
                # Since process is async but we're in sync context, use a simple sync wrapper
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                processed_query = loop.run_until_complete(self.query_processor.process(query))
                
                # Convert ProcessedQuery to dict for compatibility
                processed_dict = {
                    "original_query": processed_query.original,
                    "corrected_query": processed_query.corrected,
                    "keywords": processed_query.keywords,
                    "expanded_queries": processed_query.expanded_queries,
                    "question_type": processed_query.question_type
                }
                
                # Check cache
                st.info("💾 Checking cache...")
                cached = self.cache.get(query, st.session_state.tier, mode)
                if cached:
                    st.success("✅ Found in cache!")
                    self._display_results(cached)
                    return
                
                # Get mode settings
                mode_enum = ResearchMode(mode)
                mode_config = self.mode_manager.get_config(mode_enum)
                
                # Check premium requirement
                if mode_config.premium_only and st.session_state.tier != "premium":
                    st.error("🔒 This mode requires Premium subscription")
                    return
                
                # Search
                st.info(f"🔎 Searching {mode_config.max_sources} sources...")
                search_results = loop.run_until_complete(
                    self.search_engine.search(
                        processed_dict["corrected_query"],
                        max_results=mode_config.max_sources
                    )
                )
                
                # Convert SearchResult objects to dicts
                search_results = [r.to_dict() if hasattr(r, 'to_dict') else r for r in search_results]
                
                # Score credibility
                st.info("🎯 Scoring source credibility...")
                scored_sources = self.credibility_scorer.score_sources(search_results)
                
                # Run workflow
                st.info("🤖 Running research workflow...")
                from subscription.manager import SubscriptionTier
                tier_enum = SubscriptionTier.PREMIUM if st.session_state.tier == "premium" else SubscriptionTier.FREE
                workflow = TieredResearchOrchestrator(
                    user_id=str(st.session_state.user_id),
                    tier=tier_enum
                )
                
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(workflow.research(
                    query=processed_dict["corrected_query"],
                    output_format="all"  # Generate all available formats
                ))
                
                # Add metadata
                result["query_processing"] = processed_dict
                result["mode"] = mode
                result["sources"] = scored_sources
                result["timestamp"] = datetime.now().isoformat()
                
                # Generate charts for deep mode
                if mode == "deep":
                    st.info("📊 Generating charts...")
                    charts = self.chart_generator.generate_all_charts(result)
                    result["charts"] = charts
                
                # Get statistics from workflow
                stats = result.get("statistics", {})
                
                # Cache result
                self.cache.set(query, st.session_state.tier, mode, result)
                
                # Record usage - increment daily counter
                self.usage_tracker.increment_usage(st.session_state.user_id)
                
                # Add to research history
                output_files = result.get("output_files", {})
                report_path = output_files.get("markdown", "")
                
                self.usage_tracker.add_research_history(
                    st.session_state.user_id,
                    query,
                    st.session_state.tier,
                    stats.get("word_count", 0),
                    stats.get("sources_count", 0),
                    report_path
                )
                
                st.success("✅ Research completed!")
                self._display_results(result)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Research failed: {e}", exc_info=True)
    
    def _display_results(self, result: Dict[str, Any]):
        """Display research results."""
        st.markdown("---")
        st.subheader("📄 Research Report")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Report", "Sources", "Statistics", "Export"])
        
        with tab1:
            # Read report from generated file
            output_files = result.get("output_files", {})
            markdown_file = output_files.get("markdown", "")
            
            if markdown_file and Path(markdown_file).exists():
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    final_report = f.read()
                st.markdown(final_report)
            else:
                st.warning("Report file not found. Check output_files directory.")
                st.json(result)
        
        with tab2:
            # Display sources with credibility scores
            sources = result.get("sources", [])
            for i, source in enumerate(sources, 1):
                cred = source.get("credibility_score", {})
                score = cred.get("overall_score", 0)
                level = cred.get("credibility_level", "Unknown")
                
                with st.expander(f"{i}. {source.get('title', 'Untitled')} - Score: {score}/100 ({level})"):
                    st.write(f"**URL:** {source.get('url', 'N/A')}")
                    st.write(f"**Snippet:** {source.get('snippet', 'N/A')}")
        
        with tab3:
            # Display statistics from workflow
            mode = result.get("mode", "standard")
            stats = result.get("statistics", {})
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Research Mode", mode.capitalize())
            col2.metric("Sources Used", stats.get("sources_count", 0))
            col3.metric("Word Count", stats.get("word_count", 0))
            col4.metric("Coverage", f"{stats.get('coverage_score', 0):.1f}%")
            
            st.metric("Time Elapsed", f"{stats.get('time_elapsed', 0):.1f}s")
            st.metric("Facts Verified", stats.get("facts_count", 0))
            
            # Display charts if available
            charts = result.get("charts", {})
            if charts:
                st.subheader("📊 Visualizations")
                for chart_name, chart_path in charts.items():
                    if Path(chart_path).exists():
                        st.image(chart_path, caption=chart_name.replace("_", " ").title())
        
        with tab4:
            # Export options - files already generated by workflow
            st.subheader("📥 Generated Files")
            
            output_files = result.get("output_files", {})
            
            if output_files:
                for format_name, file_path in output_files.items():
                    if Path(file_path).exists():
                        st.success(f"✅ {format_name.upper()}: `{file_path}`")
                        
                        # Offer download for all formats
                        if format_name == "markdown":
                            with open(file_path, 'r', encoding='utf-8') as f:
                                st.download_button(
                                    label=f"⬇️ Download {format_name.upper()}",
                                    data=f.read(),
                                    file_name=Path(file_path).name,
                                    mime="text/markdown"
                                )
                        elif format_name == "pdf":
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    label=f"⬇️ Download {format_name.upper()}",
                                    data=f.read(),
                                    file_name=Path(file_path).name,
                                    mime="application/pdf"
                                )
                        elif format_name == "docx":
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    label=f"⬇️ Download {format_name.upper()}",
                                    data=f.read(),
                                    file_name=Path(file_path).name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
            else:
                st.info("No export files generated yet.")
    
    def _show_history_page(self):
        """Show research history."""
        st.title("📚 Research History")
        
        history = self.usage_tracker.get_research_history(st.session_state.user_id, limit=50)
        
        if not history:
            st.info("No research history yet. Start your first research!")
            return
        
        for idx, item in enumerate(history):
            query = item.get('query', 'Unknown')
            timestamp = item.get('created_at', '')
            report_path = item.get('report_path', '')
            
            with st.expander(f"{query} - {timestamp}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Tier:** {item.get('tier', 'free').capitalize()}")
                    st.write(f"**Sources:** {item.get('sources_count', 'N/A')}")
                    st.write(f"**Word Count:** {item.get('word_count', 'N/A')}")
                
                with col2:
                    from pathlib import Path
                    
                    # Use the stored report path to find all related files
                    if report_path and Path(report_path).exists():
                        base_path = Path(report_path).parent
                        base_name = Path(report_path).stem
                        
                        # Look for markdown file
                        md_file = base_path / f"{base_name}.md"
                        if md_file.exists():
                            with open(md_file, 'r', encoding='utf-8') as f:
                                st.download_button(
                                    label="📄 MD",
                                    data=f.read(),
                                    file_name=md_file.name,
                                    mime="text/markdown",
                                    key=f"md_{idx}_{md_file.name}",
                                    use_container_width=True
                                )
                        
                        # Look for PDF file
                        pdf_file = base_path / f"{base_name}.pdf"
                        if pdf_file.exists():
                            with open(pdf_file, 'rb') as f:
                                st.download_button(
                                    label="📕 PDF",
                                    data=f.read(),
                                    file_name=pdf_file.name,
                                    mime="application/pdf",
                                    key=f"pdf_{idx}_{pdf_file.name}",
                                    use_container_width=True
                                )
                        
                        # Look for DOCX file
                        docx_file = base_path / f"{base_name}.docx"
                        if docx_file.exists():
                            with open(docx_file, 'rb') as f:
                                st.download_button(
                                    label="📘 DOCX",
                                    data=f.read(),
                                    file_name=docx_file.name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"docx_{idx}_{docx_file.name}",
                                    use_container_width=True
                                )
                    else:
                        st.caption("Files not available")
    
    def _show_statistics_page(self):
        """Show usage statistics."""
        st.title("📊 Usage Statistics")
        
        # Daily usage
        usage_count = self.usage_tracker.get_usage_today(st.session_state.user_id)
        limit = "Unlimited" if st.session_state.tier == "premium" else "5"
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Today's Researches", f"{usage_count} / {limit}")
        
        with col2:
            remaining = "Unlimited" if st.session_state.tier == "premium" else str(5 - usage_count)
            st.metric("Remaining", remaining)
        
        # Cache stats
        st.subheader("💾 Cache Statistics")
        cache_stats = self.cache.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cached Queries", cache_stats['total_entries'])
        with col2:
            st.metric("Cache Hits", cache_stats['total_hits'])
        with col3:
            st.metric("Cache Size", f"{cache_stats['total_size_mb']:.2f} MB")
        
        if st.button("🗑️ Clear Cache"):
            self.cache.base_cache.clear_all()
            st.success("Cache cleared!")
            st.rerun()
    
    def _show_settings_page(self):
        """Show settings."""
        st.title("⚙️ Settings")
        
        # Account info
        user = self.db.get_user(st.session_state.user_id)
        
        st.subheader("Account Information")
        st.write(f"**Username:** {user.get('username', 'N/A')}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")
        st.write(f"**Tier:** {user.get('tier', 'free').upper()}")
        st.write(f"**Created:** {user.get('created_at', 'N/A')}")
        
        # Upgrade option
        if st.session_state.tier == "free":
            st.markdown("---")
            self._show_upgrade_page()
    
    def _show_upgrade_page(self):
        """Show premium upgrade page."""
        st.subheader("⭐ Upgrade to Premium")
        
        # Feature comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🆓 Free Plan")
            st.markdown("""
            - ✅ 5 researches per day
            - ✅ Quick & Standard modes
            - ✅ PDF & Markdown exports
            - ✅ 2-5 sources per research
            - ✅ Basic citations
            - ✅ Up to 2000 words
            """)
            st.markdown("**Price:** $0/month")
        
        with col2:
            st.markdown("### 💎 Premium Plan")
            st.markdown("""
            - ⭐ **Unlimited researches**
            - ⭐ **Deep Research mode**
            - ⭐ **PDF, DOCX & Markdown exports**
            - ⭐ **15+ sources per research**
            - ⭐ **APA, MLA, Chicago citations**
            - ⭐ **Up to 5000+ words**
            - ⭐ **Advanced fact-checking**
            - ⭐ **Priority support**
            """)
            st.markdown("**Price:** $29.99/month")
        
        st.markdown("---")
        
        # Subscription form
        st.subheader("💳 Payment Information")
        
        with st.form("subscription_form"):
            st.text_input("Card Number", placeholder="1234 5678 9012 3456")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.text_input("Expiry Month", placeholder="MM")
            with col2:
                st.text_input("Expiry Year", placeholder="YY")
            with col3:
                st.text_input("CVV", placeholder="123", type="password")
            
            st.text_input("Cardholder Name", placeholder="Rahul Sharma")
            st.text_input("Billing Address", placeholder="123 MG Road")
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("City", placeholder="Mumbai")
            with col2:
                st.text_input("PIN Code", placeholder="400001")
            
            st.markdown("---")
            
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submit = st.form_submit_button("💎 Subscribe to Premium - $29.99/month", use_container_width=True, type="primary")
            
            if submit:
                if not agree:
                    st.error("Please agree to the Terms of Service")
                else:
                    st.info("🚧 **Payment Integration Coming Soon!**")
                    st.markdown("""
                    We're working on integrating secure payment processing. 
                    
                    For now, please contact our support team to manually upgrade your account:
                    - Email: gargsahil156@gmail.com
                    - Phone: +91 9464657352
                    
                    Thank you for your interest in Premium! 🙏
                    """)


def main():
    """Main entry point."""
    app = AutoResearchApp()
    
    if not st.session_state.authenticated:
        app.show_login_page()
    else:
        app.show_dashboard()


if __name__ == "__main__":
    main()
