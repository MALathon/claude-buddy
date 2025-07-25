#!/usr/bin/env python3
"""Context7 documentation enhancement hook - proactively provides current docs BEFORE code generation."""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from ..base import BaseHook, ConcurrencyManager
    from ..unified_logger import get_unified_logger, ComponentType, LogLevel
    from ..external_loader import get_external_loader
    from process_timeouts import TIMEOUTS
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from hooks.base import BaseHook, ConcurrencyManager
    from hooks.unified_logger import get_unified_logger, ComponentType, LogLevel
    from hooks.external_loader import get_external_loader
    from process_timeouts import TIMEOUTS


class Context7DocsHook(BaseHook):
    """Hook that proactively enhances Claude's context with current documentation BEFORE code generation.
    
    Research-based timing: Context7 provides maximum value when called BEFORE Claude writes code,
    not after. This prevents hallucinated APIs and ensures current documentation context.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        concurrency_manager: Optional[ConcurrencyManager] = None,
    ) -> None:
        """Initialize Context7 documentation enhancement hook."""
        super().__init__(config, concurrency_manager)
        
        # Configuration optimized for proactive enhancement with type validation
        self.proactive_enhancement = self._get_bool_config(config, "proactive_enhancement", True)
        self.max_tokens_per_library = self._get_int_config(config, "max_tokens_per_library", 8000, min_val=1)
        self.max_libraries = self._get_int_config(config, "max_libraries", 3, min_val=1)
        self.cache_duration_hours = self._get_float_config(config, "cache_duration_hours", 24.0, min_val=0.1)
        
        # Priority libraries for fast-moving, version-critical documentation
        priority_libs = config.get("priority_libraries", [
            "react", "next.js", "typescript", "react-query", "tailwindcss",
            "django", "fastapi", "nextauth.js", "prisma"
        ])
        # Ensure it's a list
        if isinstance(priority_libs, list):
            self.priority_libraries = set(priority_libs)
        else:
            self.priority_libraries = set([
                "react", "next.js", "typescript", "react-query", "tailwindcss",
                "django", "fastapi", "nextauth.js", "prisma"
            ])
        
        # Resource pool for concurrency management
        self.resource_pool = config.get("resource_pool", "documentation")
        
        # External tool management
        self.external_loader = get_external_loader()
        
        # Documentation cache with timestamp
        self.doc_cache = {}
    
    def _get_bool_config(self, config: Dict[str, Any], key: str, default: bool) -> bool:
        """Get boolean config value with type validation."""
        value = config.get(key, default)
        if isinstance(value, bool):
            return value
        return default
    
    def _get_int_config(self, config: Dict[str, Any], key: str, default: int, min_val: Optional[int] = None) -> int:
        """Get integer config value with type validation."""
        value = config.get(key, default)
        if isinstance(value, int) and (min_val is None or value >= min_val):
            return value
        return default
    
    def _get_float_config(self, config: Dict[str, Any], key: str, default: float, min_val: Optional[float] = None) -> float:
        """Get float config value with type validation."""
        value = config.get(key, default)
        if isinstance(value, (int, float)) and (min_val is None or value >= min_val):
            return float(value)
        return default
        
    def process_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process event with research-based timing optimization."""
        logger = get_unified_logger()
        
        if not self.enabled:
            return True, ""
            
        # Check if Context7 MCP server is available
        if not self.external_loader.is_tool_available("context7"):
            logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                      "⚠️ Context7 MCP server not available - skipping enhancement")
            return True, ""
            
        event_type = event_data.get("event_type")
        
        # PRIMARY: Proactive enhancement before code generation
        if event_type == "PreToolUse" and self.proactive_enhancement:
            return self._proactive_enhancement(event_data)
            
        # SECONDARY: Reactive analysis after dependency changes
        elif event_type == "PostToolUse":
            return self._reactive_analysis(event_data)
            
        return True, ""
        
    def _proactive_enhancement(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """PROACTIVE: Enhance context BEFORE Claude writes code (optimal pattern)."""
        if not self.is_applicable_pretooluse(event_data):
            return True, ""
            
        # Use concurrency management
        if self.concurrency_manager:
            with self.concurrency_manager.acquire_resource(
                self.resource_pool,
                {"operation": "proactive_docs", "tool": event_data.get("tool_name")},
                timeout=TIMEOUTS.for_mcp_server()
            ) as acquired:
                if not acquired:
                    return True, ""
                return self._fetch_proactive_documentation(event_data)
        else:
            return self._fetch_proactive_documentation(event_data)
            
    def _reactive_analysis(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """REACTIVE: Analyze new dependencies after file operations."""
        if not self.is_applicable_posttooluse(event_data):
            return True, ""
            
        # Lighter weight for reactive analysis
        return self._analyze_new_dependencies(event_data)
        
    def _analyze_new_dependencies(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Analyze new dependencies after file operations."""
        logger = get_unified_logger()
        
        try:
            file_path = event_data.get("tool_input", {}).get("file_path", "")
            
            # Read the dependency file to extract new libraries
            if not Path(file_path).exists():
                return True, ""
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract new dependencies
            new_libraries = self._extract_dependencies(content)
            
            if new_libraries:
                context_enhancements = []
                for library in list(new_libraries)[:2]:  # Limit for reactive analysis
                    docs = self._get_library_documentation(library, event_data)
                    if docs:
                        context_enhancements.append(docs)
                        
                if context_enhancements:
                    message = self._format_context_enhancement(context_enhancements)
                    return True, f"📚 New dependencies detected:\n{message}"
                    
            return True, ""
            
        except Exception as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                      f"❌ Error analyzing new dependencies: {e}")
            return True, ""
        
    def _fetch_proactive_documentation(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Fetch documentation proactively before code generation."""
        logger = get_unified_logger()
        try:
            # Detect libraries that need documentation
            libraries = self._detect_relevant_libraries(event_data)
            if not libraries:
                return True, ""
                
            logger.log(ComponentType.CONTEXT7, LogLevel.INFO, 
                      f"📚 Context7: Detected libraries {libraries}")
            
            # Fetch documentation for detected libraries
            context_enhancements = []
            
            for library in libraries:
                docs = self._get_library_documentation(library, event_data)
                if docs:
                    context_enhancements.append(docs)
                    
            if context_enhancements:
                message = self._format_context_enhancement(context_enhancements)
                return True, message
            else:
                return True, ""
                
        except Exception as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                      f"❌ Context7 enhancement error: {e}")
            return True, ""
            
    def _detect_relevant_libraries(self, event_data: Dict[str, Any]) -> List[str]:
        """Detect libraries that need current documentation."""
        tool_input = event_data.get("tool_input", {})
        detected_libs = set()
        
        # Check different content sources
        content_sources = [
            tool_input.get("content", ""),
            tool_input.get("new_string", ""),
            tool_input.get("file_path", "")
        ]
        
        for content in content_sources:
            if not content:
                continue
                
            # Detect package.json or requirements.txt analysis
            if self._is_dependency_file(content):
                detected_libs.update(self._extract_dependencies(content))
                
            # Detect import statements
            detected_libs.update(self._extract_imports(content))
            
            # Detect framework patterns
            detected_libs.update(self._detect_framework_patterns(content))
            
        # Prioritize important libraries and limit count
        prioritized = self._prioritize_libraries(list(detected_libs))
        return prioritized[:self.max_libraries]
        
    def _is_dependency_file(self, content: str) -> bool:
        """Check if content is from a dependency file."""
        dependency_indicators = [
            '"dependencies":', '"devDependencies":',  # package.json
            'install_requires', 'requirements.txt',   # Python
            '[dependencies]', 'Cargo.toml'            # Rust
        ]
        return any(indicator in content for indicator in dependency_indicators)
        
    def _extract_dependencies(self, content: str) -> Set[str]:
        """Extract library names from dependency files."""
        libs = set()
        
        # package.json dependencies
        if '"dependencies":' in content or '"devDependencies":' in content:
            for match in re.finditer(r'"([^"@]+)"\s*:', content):
                lib = match.group(1)
                if not lib.startswith('@types/'):
                    libs.add(lib)
                    
        # Python requirements
        for match in re.finditer(r'^([a-zA-Z][a-zA-Z0-9-_]*)', content, re.MULTILINE):
            lib = match.group(1).lower()
            if lib not in ['pip', 'setuptools', 'wheel']:
                libs.add(lib)
                
        return libs
        
    def _extract_imports(self, content: str) -> Set[str]:
        """Extract library names from import statements."""
        libs = set()
        
        # JavaScript/TypeScript imports
        js_patterns = [
            r'import\s+.*?\s+from\s+["\']([^"\']+)["\']',
            r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'import\s*\(\s*["\']([^"\']+)["\']\s*\)'
        ]
        
        for pattern in js_patterns:
            for match in re.finditer(pattern, content):
                lib = match.group(1).split('/')[0]
                if not lib.startswith('.') and not lib.startswith('@types/'):
                    libs.add(lib)
                    
        # Python imports
        python_patterns = [
            r'from\s+([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)',
            r'import\s+([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)'
        ]
        
        for pattern in python_patterns:
            for match in re.finditer(pattern, content):
                lib = match.group(1).split('.')[0]
                # Filter out standard library modules
                stdlib_modules = {
                    'os', 'sys', 'json', 'typing', 'pathlib', 'collections',
                    're', 'datetime', 'time', 'random', 'math', 'itertools',
                    'functools', 'operator', 'copy', 'io', 'pickle', 'csv',
                    'sqlite3', 'urllib', 'http', 'email', 'html', 'xml',
                    'unittest', 'doctest', 'pdb', 'profile', 'timeit',
                    'argparse', 'logging', 'warnings', 'traceback', 'inspect',
                    'ast', 'types', 'enum', 'dataclasses', 'abc', 'asyncio',
                    'concurrent', 'multiprocessing', 'threading', 'queue',
                    'socket', 'ssl', 'select', 'signal', 'subprocess', 'shutil',
                    'tempfile', 'glob', 'fnmatch', 'fileinput', 'filecmp',
                    'configparser', 'hashlib', 'hmac', 'secrets', 'uuid',
                    'contextlib', 'decimal', 'fractions', 'statistics', 'cmath',
                    'array', 'bisect', 'heapq', 'weakref', 'copyreg', 'shelve',
                    'marshal', 'dbm', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile',
                    'tarfile', 'readline', 'rlcompleter', 'pty', 'fcntl', 'termios',
                    'tty', 'syslog', 'platform', 'errno', 'ctypes', 'struct',
                    'codecs', 'encodings', 'unicodedata', 'stringprep', 'locale',
                    'gettext', 'optparse', 'getopt', 'textwrap', 'curses', 'cmd',
                    'shlex', 'tkinter', 'turtle', 'pydoc', 'test', 'bdb', 'faulthandler',
                    'builtins', '__future__', '__main__', '_thread', 'gc', 'importlib',
                    'pkgutil', 'modulefinder', 'runpy', 'parser', 'symbol', 'token',
                    'keyword', 'tokenize', 'tabnanny', 'pyclbr', 'py_compile', 'compileall',
                    'dis', 'pickletools', 'distutils', 'site', 'venv', 'numbers',
                    'cgi', 'cgitb', 'wsgiref', 'smtplib', 'smtpd', 'telnetlib',
                    'uuid', 'socketserver', 'http', 'xmlrpc', 'ipaddress', 'ftplib',
                    'poplib', 'imaplib', 'nntplib', 'pathlib', 'Path'
                }
                if lib not in stdlib_modules:
                    libs.add(lib)
                    
        return libs
        
    def _detect_framework_patterns(self, content: str) -> Set[str]:
        """Detect framework usage patterns."""
        libs = set()
        
        framework_patterns = {
            'react': [r'useState', r'useEffect', r'React\.', r'jsx', r'tsx'],
            'next.js': [r'next/', r'getStaticProps', r'getServerSideProps', r'NextApiRequest'],
            'django': [r'django\.', r'models\.Model', r'views\.', r'urls\.py'],
            'fastapi': [r'FastAPI', r'@app\.', r'Depends\(', r'APIRouter'],
            'flask': [r'Flask', r'@app\.route', r'request\.'],
            'express': [r'express', r'app\.get', r'app\.post', r'req\,\s*res'],
            'vue': [r'Vue\.', r'v-if', r'v-for', r'@click'],
            'angular': [r'@Component', r'@Injectable', r'ngOnInit']
        }
        
        for framework, patterns in framework_patterns.items():
            if any(re.search(pattern, content) for pattern in patterns):
                libs.add(framework)
                
        return libs
        
    def _prioritize_libraries(self, libraries: List[str]) -> List[str]:
        """Prioritize libraries based on importance and frequency."""
        # Separate priority vs regular libraries
        priority = [lib for lib in libraries if lib in self.priority_libraries]
        regular = [lib for lib in libraries if lib not in self.priority_libraries]
        
        # Priority libraries first, then regular
        return priority + regular
        
    def _get_library_documentation(self, library: str, event_data: Dict[str, Any]) -> Optional[str]:
        """Fetch documentation for a library via Context7 MCP."""
        logger = get_unified_logger()
        
        try:
            # Check cache first
            cache_key = f"{library}_{self._infer_topic(event_data)}"
            if self._is_cache_valid(cache_key):
                return self.doc_cache[cache_key]["content"]
                
            # Resolve library ID
            lib_id = self._resolve_library_id(library)
            if not lib_id:
                return None
                
            # Get documentation with topic filtering
            topic = self._infer_topic(event_data)
            docs = self._fetch_library_docs(lib_id, topic)
            
            if docs:
                # Cache the result
                import time
                self.doc_cache[cache_key] = {
                    "content": docs,
                    "timestamp": time.time()
                }
                return docs
                
            return None
            
        except Exception as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                      f"⚠️ Could not fetch docs for {library}: {e}")
            return None
            
    def _resolve_library_id(self, library: str) -> Optional[str]:
        """Resolve library name to Context7 ID."""
        logger = get_unified_logger()
        
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "resolve-library-id",
                    "arguments": {"libraryName": library}
                },
                "id": 1
            }
            
            response = self._call_mcp_server(mcp_request)
            if response and "result" in response:
                # The result contains content with library information
                content = response["result"].get("content")
                if content and isinstance(content, list) and len(content) > 0:
                    # Parse the response to extract the best library ID
                    text = content[0].get("text", "")
                    resolved_id = self._select_best_library_match(text, library)
                    if resolved_id:
                        logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                                  f"🔍 Resolved {library} to {resolved_id}")
                        return resolved_id
                    
            # Fallback to library name if resolution fails
            return library
            
        except Exception as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                      f"⚠️ Could not resolve library ID for {library}: {e}")
            return library  # Fallback to original name
            
    def _fetch_library_docs(self, lib_id: str, topic: Optional[str] = None) -> Optional[str]:
        """Fetch documentation for library ID."""
        logger = get_unified_logger()
        
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get-library-docs",
                    "arguments": {
                        "context7CompatibleLibraryID": lib_id,
                        "tokens": self.max_tokens_per_library
                    }
                },
                "id": 1
            }
            
            if topic:
                mcp_request["params"]["arguments"]["topic"] = topic
                
            response = self._call_mcp_server(mcp_request)
            if response and "result" in response:
                # The result contains content with documentation
                content = response["result"].get("content")
                if content and isinstance(content, list) and len(content) > 0:
                    # Extract text from the content array
                    docs = content[0].get("text", "")
                    if docs:
                        logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                                  f"📖 Fetched documentation for {lib_id} ({len(docs)} chars)")
                        return docs
                    
            return None
            
        except Exception as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                      f"⚠️ Could not fetch docs for {lib_id}: {e}")
            return None
            
    def _infer_topic(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Infer documentation topic from context."""
        tool_input = event_data.get("tool_input", {})
        content = tool_input.get("content", "") or tool_input.get("new_string", "")
        
        topic_keywords = {
            "authentication": ["auth", "login", "token", "session", "passport"],
            "routing": ["route", "router", "path", "endpoint", "api"],
            "testing": ["test", "spec", "mock", "jest", "pytest"],
            "hooks": ["usestate", "useeffect", "usecallback", "usememo"],
            "components": ["component", "render", "props", "jsx", "tsx"],
            "database": ["db", "query", "model", "schema", "migration"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content.lower() for keyword in keywords):
                return topic
                
        return None
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached documentation is still valid."""
        if cache_key not in self.doc_cache:
            return False
            
        import time
        cache_age_hours = (time.time() - self.doc_cache[cache_key]["timestamp"]) / 3600
        return cache_age_hours < self.cache_duration_hours
        
    def _format_context_enhancement(self, enhancements: List[str]) -> str:
        """Format context enhancements for display."""
        if not enhancements:
            return ""
            
        # Extract key information from each enhancement and format concisely
        formatted_parts = ["📚 Context7: Enhanced context with current documentation", ""]
        
        for i, enhancement in enumerate(enhancements[:2]):  # Limit to 2 libraries for readability
            # Extract library info (first few lines usually contain the key info)
            lines = enhancement.split('\n')
            
            # Find title and description
            title = ""
            description = ""
            code_snippet = ""
            
            for line in lines[:20]:  # Look at first 20 lines
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('DESCRIPTION:'):
                    description = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('CODE:') and not code_snippet:
                    # Find the first code block
                    code_start = lines.index(line)
                    code_lines = []
                    for code_line in lines[code_start+1:code_start+6]:  # Take up to 5 lines
                        if code_line.strip() and not code_line.startswith('```'):
                            code_lines.append(code_line)
                        elif code_line.startswith('```') and code_lines:
                            break
                    code_snippet = '\n'.join(code_lines)
                    break
            
            # Create a concise summary
            if title or description:
                formatted_parts.append(f"🔸 **{title[:60]}{'...' if len(title) > 60 else ''}**")
                if description:
                    formatted_parts.append(f"   {description[:100]}{'...' if len(description) > 100 else ''}")
                if code_snippet:
                    formatted_parts.append(f"   ```\n   {code_snippet[:150]}{'...' if len(code_snippet) > 150 else ''}\n   ```")
                formatted_parts.append("")
        
        if len(enhancements) > 2:
            formatted_parts.append(f"... and {len(enhancements) - 2} more documentation entries available")
            
        formatted_parts.append("💡 Full documentation available for enhanced code completion")
        
        return "\n".join(formatted_parts)
        
    def is_applicable(self, event_data: Dict[str, Any]) -> bool:
        """Check if this hook should process the event."""
        # Process both PreToolUse and PostToolUse for different scenarios
        event_type = event_data.get("event_type")
        if event_type not in ["PreToolUse", "PostToolUse"]:
            return False
            
        tool_name = event_data.get("tool_name", "")
        
        # PreToolUse: Enhance context before code operations
        if event_type == "PreToolUse":
            return tool_name in ["Write", "Edit", "MultiEdit"]
            
        # PostToolUse: Analyze new dependencies
        if event_type == "PostToolUse":
            return tool_name in ["Read"] and self._is_dependency_file_path(
                event_data.get("tool_input", {}).get("file_path", "")
            )
            
        return False
        
    def is_applicable_pretooluse(self, event_data: Dict[str, Any]) -> bool:
        """Check if PreToolUse event should be processed."""
        tool_name = event_data.get("tool_name", "")
        return tool_name in ["Write", "Edit", "MultiEdit"]
        
    def is_applicable_posttooluse(self, event_data: Dict[str, Any]) -> bool:
        """Check if PostToolUse event should be processed."""
        tool_name = event_data.get("tool_name", "")
        if tool_name != "Read":
            return False
            
        file_path = event_data.get("tool_input", {}).get("file_path", "")
        return self._is_dependency_file_path(file_path)
        
    def _is_dependency_file_path(self, file_path: str) -> bool:
        """Check if file path indicates a dependency file."""
        dependency_files = [
            "package.json", "requirements.txt", "Cargo.toml",
            "pyproject.toml", "composer.json", "go.mod"
        ]
        return any(dep_file in file_path for dep_file in dependency_files)
        
    def _select_best_library_match(self, text: str, original_library: str) -> Optional[str]:
        """Select the best library match from Context7 response."""
        import re
        
        # Split response into entries
        entries = text.split('----------')
        
        best_entry = None
        best_score = 0
        
        for entry in entries:
            if 'Context7-compatible library ID:' not in entry:
                continue
                
            # Extract title
            title_match = re.search(r'Title: ([^\n]+)', entry)
            title = title_match.group(1).strip() if title_match else ""
            
            # Extract trust score
            score_match = re.search(r'Trust Score: ([\d.]+)', entry)
            score = float(score_match.group(1)) if score_match else 0
            
            # Calculate relevance score
            relevance_score = 0
            
            # Exact match gets highest priority
            if title.lower() == original_library.lower():
                relevance_score = 100 + score
            # Starts with the library name
            elif title.lower().startswith(original_library.lower()):
                relevance_score = 80 + score
            # Contains the library name
            elif original_library.lower() in title.lower():
                relevance_score = 60 + score
            else:
                relevance_score = score
                
            # Update best match if this is better
            if relevance_score > best_score:
                best_score = relevance_score
                best_entry = entry
        
        if best_entry:
            lib_id_match = re.search(r'Context7-compatible library ID: ([^\n]+)', best_entry)
            return lib_id_match.group(1).strip() if lib_id_match else None
        
        return None
        
    def _call_mcp_server(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Context7 MCP server with JSON-RPC request."""
        logger = get_unified_logger()
        
        try:
            tool_info = self.external_loader.get_tool_info("context7")
            if not tool_info or not tool_info.get("available"):
                logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                          "⚠️ Context7 MCP server not available")
                return None
                
            mcp_config = tool_info.get("mcp_config", {})
            transport = mcp_config.get("transport", "stdio")
            
            if transport == "http":
                # Use HTTP transport (remote server)
                url = mcp_config.get("url")
                if not url:
                    logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                              "❌ No URL configured for Context7 HTTP transport")
                    return None
                    
                logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                          f"🌐 Calling Context7 MCP via HTTP: {url}")
                logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                          f"📤 Request: {json.dumps(request)[:200]}...")
                
                import requests
                response = requests.post(
                    url,
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    timeout=TIMEOUTS.for_mcp_server()
                )
                
                if response.status_code != 200:
                    logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                              f"❌ Context7 HTTP error: {response.status_code} - {response.text[:200]}...")
                    return None
                    
                result = response.json()
                logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                          f"📥 HTTP response: {json.dumps(result, indent=2)[:200]}...")
                return result
                
            else:
                # Use stdio transport (local server) with proper MCP initialization
                command = mcp_config.get("command")
                args = mcp_config.get("args", [])
                
                if not command:
                    logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                              "❌ No command configured for Context7 MCP server")
                    return None
                    
                # Build full command with stdio transport
                full_command = [command] + args + ["--transport", "stdio"]
                
                logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                          f"🔧 Calling Context7 MCP: {' '.join(full_command)}")
                
                # Start MCP server process
                import subprocess
                process = subprocess.Popen(
                    full_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                try:
                    # Step 1: Initialize the MCP server
                    init_request = {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "roots": {"listChanged": True},
                                "sampling": {}
                            },
                            "clientInfo": {
                                "name": "claude-buddy",
                                "version": "1.0.0"
                            }
                        },
                        "id": 0
                    }
                    
                    logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                              f"📤 Sending initialize: {json.dumps(init_request)[:200]}...")
                    process.stdin.write(json.dumps(init_request) + "\n")
                    process.stdin.flush()
                    
                    # Read initialization response
                    init_response = process.stdout.readline()
                    logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                              f"📥 Init response: {init_response[:200]}...")
                    
                    # Step 2: Send initialized notification
                    initialized_notification = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {}
                    }
                    
                    logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                              f"📤 Sending initialized: {json.dumps(initialized_notification)}")
                    process.stdin.write(json.dumps(initialized_notification) + "\n")
                    process.stdin.flush()
                    
                    # Step 3: Send the actual tool request
                    logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                              f"📤 Sending request: {json.dumps(request)[:200]}...")
                    process.stdin.write(json.dumps(request) + "\n")
                    process.stdin.flush()
                    
                    # Read tool response
                    tool_response = process.stdout.readline()
                    logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                              f"📥 Tool response: {tool_response[:200]}...")
                    
                    # Close the process
                    process.stdin.close()
                    process.wait(timeout=TIMEOUTS.for_mcp_server())
                    
                    if tool_response:
                        response = json.loads(tool_response)
                        logger.log(ComponentType.CONTEXT7, LogLevel.DEBUG, 
                                  f"📋 Parsed response: {json.dumps(response, indent=2)[:200]}...")
                        return response
                        
                    return None
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                              "⏱️ Context7 MCP server request timed out (subprocess)")
                    return None
                except Exception as e:
                    process.kill()
                    process.wait()
                    logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                              f"❌ Error in MCP communication: {e}")
                    return None
            
        except requests.RequestException as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                      f"❌ Context7 HTTP request error: {e}")
            return None
        except subprocess.TimeoutExpired:
            logger.log(ComponentType.CONTEXT7, LogLevel.WARNING, 
                      "⏱️ Context7 MCP server request timed out")
            return None
        except json.JSONDecodeError as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                      f"❌ Invalid JSON response from Context7 MCP server: {e}")
            logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                      f"📄 Raw response: {response.text if 'response' in locals() else result.stdout if 'result' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.log(ComponentType.CONTEXT7, LogLevel.ERROR, 
                      f"❌ Error calling Context7 MCP server: {e}")
            return None
            
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        schema = super().get_config_schema()
        schema["properties"].update({
            "auto_detect_libraries": {
                "type": "boolean",
                "description": "Automatically detect libraries and fetch documentation",
                "default": True
            },
            "max_tokens_per_library": {
                "type": "integer",
                "description": "Maximum tokens to fetch per library",
                "default": 8000,
                "minimum": 1000,
                "maximum": 20000
            },
            "max_libraries": {
                "type": "integer",
                "description": "Maximum number of libraries to enhance per event",
                "default": 3,
                "minimum": 1,
                "maximum": 10
            },
            "cache_duration_hours": {
                "type": "integer",
                "description": "Hours to cache documentation",
                "default": 24,
                "minimum": 1,
                "maximum": 168
            },
            "priority_libraries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Libraries to prioritize for documentation",
                "default": ["react", "next.js", "typescript", "python", "django", "fastapi"]
            },
            "resource_pool": {
                "type": "string",
                "description": "Concurrency pool name",
                "default": "documentation"
            }
        })
        return schema


# Factory function for registry
def create_hook(
    config: Dict[str, Any],
    concurrency_manager: Optional[ConcurrencyManager] = None,
) -> Context7DocsHook:
    """Create Context7 documentation enhancement hook instance."""
    return Context7DocsHook(config, concurrency_manager)