import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

// --- API Client ---
const apiClient = {
  login: async (username, password) => {
    const response = await fetch('/api/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
    }
    return response.json();
  },
  signup: async (username, password, email) => {
    const response = await fetch('/api/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, email }),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.username?.[0] || 'Signup failed');
    }
    return response.json();
  },
  getDocuments: async (token) => {
    const response = await fetch('/api/documents/', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
  },
  getDocumentDetails: async (token, docId) => {
     const response = await fetch(`/api/documents/${docId}/`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch document details');
    return response.json();
  },
  uploadDocument: async (token, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('/api/documents/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    });
    if (!response.ok) throw new Error('File upload failed');
    return response.json();
  },
  searchDocuments: async (token, query) => {
    const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
        headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Search failed');
    return response.json();
  },
  generateContent: async (token, docId, contentType) => {
    const response = await fetch(`/api/documents/${docId}/generate/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type: contentType })
    });
    if (!response.ok) throw new Error(`Failed to generate ${contentType}`);
    return response.json();
  }
};

// --- SVG Icons ---
const icons = {
  documents: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>,
  settings: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>,
  profile: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>,
  search: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>,
  sun: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>,
  moon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>,
  spinner: <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>,
  success: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>,
  fail: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>,
};


// --- React Components ---

const LoginPage = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [isSigningUp, setIsSigningUp] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      if (isSigningUp) {
        await apiClient.signup(username, password, email);
        const { access, refresh } = await apiClient.login(username, password);
        onLogin({ access, refresh, username }, rememberMe);
      } else {
        const { access, refresh } = await apiClient.login(username, password);
        onLogin({ access, refresh, username }, rememberMe);
      }
    } catch (err) {
      setError(err.message || 'An error occurred.');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="w-full max-w-md p-8 space-y-8 bg-white dark:bg-gray-850 rounded-xl shadow-lg border border-gray-200 dark:border-gray-950">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900 dark:text-gray-100">
            {isSigningUp ? 'Create an Account' : 'Sign in'}
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <div className="space-y-4">
            <input id="username" name="username" type="text" required className="appearance-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-700 placeholder-gray-500 text-gray-900 dark:text-gray-200 bg-gray-50 dark:bg-gray-700 rounded-xl focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            {isSigningUp && (
              <input id="email" name="email" type="email" required className="appearance-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-700 placeholder-gray-500 text-gray-900 dark:text-gray-200 bg-gray-50 dark:bg-gray-700 rounded-xl focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} />
            )}
            <input id="password" name="password" type="password" required className="appearance-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-700 placeholder-gray-500 text-gray-900 dark:text-gray-200 bg-gray-50 dark:bg-gray-700 rounded-xl focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
           <div className="flex items-center justify-between pt-2">
            {!isSigningUp && (
              <div className="flex items-center">
                <input id="remember-me" name="remember-me" type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="h-4 w-4 text-gray-600 focus:ring-gray-500 border-gray-300 rounded" />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900 dark:text-gray-300">Remember me</label>
          </div>
            )}
            <div className={`text-sm ${isSigningUp ? 'w-full text-center' : ''}`}>
               <button type="button" onClick={() => setIsSigningUp(!isSigningUp)} className="font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors">
                {isSigningUp ? 'Already have an account? Sign in' : 'Don\'t have an account? Sign up'}
              </button>
            </div>
          </div>
          <div className="pt-4">
            <button type="submit" disabled={isLoading} className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gray-800 dark:bg-gray-700 hover:bg-gray-700 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:bg-gray-400 dark:disabled:bg-gray-600 transition-colors">
              {isLoading ? 'Processing...' : (isSigningUp ? 'Sign up' : 'Sign in')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const Sidebar = ({ activePage, setActivePage }) => {
    const navItems = [
        { name: 'Documents', icon: icons.documents },
        { name: 'Settings', icon: icons.settings },
        { name: 'Profile', icon: icons.profile },
    ];
  return (
        <aside className="w-64 flex-shrink-0 bg-gray-50 dark:bg-gray-950 border-r border-gray-200 dark:border-gray-950 p-4 flex flex-col">
            <div className="font-bold text-xl mb-8 text-gray-900 dark:text-gray-100 pl-3">Synapse</div>
            <nav className="flex flex-col space-y-2">
                {navItems.map(item => (
                    <button key={item.name} onClick={() => setActivePage(item.name)} 
                        className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${activePage === item.name ? 'bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-850'}`}>
                        {item.icon}
                        <span>{item.name}</span>
            </button>
          ))}
        </nav>
        </aside>
    );
};

const Header = ({ username, onLogout, isDarkMode, onToggleDarkMode, onSearch }) => {
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearch = (e) => {
        if (e.key === 'Enter' && searchQuery) {
            onSearch(searchQuery);
        }
    };

  return (
        <header className="flex-shrink-0 h-16 flex items-center justify-between px-6 border-b border-gray-300 dark:border-gray-950 bg-white dark:bg-gray-850">
            <div className="flex-1 max-w-lg mx-auto">
          <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 dark:text-gray-500">
                        {icons.search}
                    </div>
                    <input type="search" placeholder="Semantic Search..." 
                           className="w-full pl-12 pr-4 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-600 focus:border-transparent text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
              value={searchQuery}
                           onChange={(e) => setSearchQuery(e.target.value)}
                           onKeyDown={handleSearch}
            />
          </div>
        </div>
        <div className="flex items-center space-x-4">
                <button onClick={onToggleDarkMode} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 transition-colors">
                    {isDarkMode ? icons.sun : icons.moon}
          </button>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{username}</span>
                <button onClick={onLogout} className="text-sm px-3 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 transition-colors">Logout</button>
        </div>
        </header>
    );
};

const DocumentList = ({ documents, activeDocument, onSelectDocument, onUpload }) => {
    const fileInputRef = useRef(null);

    const handleUploadClick = () => {
        fileInputRef.current.click();
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            onUpload(file);
        }
    };

    const StatusIcon = ({ status }) => {
        switch (status) {
            case 'processing': return <div className="text-gray-400" title="Processing...">{icons.spinner}</div>;
            case 'completed': return <div className="text-green-500" title="Completed">{icons.success}</div>;
            case 'failed': return <div className="text-red-500" title="Failed">{icons.fail}</div>;
            default: return null;
        }
    };

  return (
        <div className="w-80 flex-shrink-0 border-r border-gray-200 dark:border-gray-950 overflow-y-auto bg-white dark:bg-gray-850">
      <div className="p-4">
                <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
                <button onClick={handleUploadClick} className="w-full bg-gray-800 dark:bg-gray-700 text-white py-2 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors">
                    + Upload New
        </button>
            </div>
            <div className="flex flex-col">
                {documents.map(doc => (
                    <button key={doc.id} onClick={() => onSelectDocument(doc)}
                        className={`p-4 text-left border-l-4 transition-colors ${activeDocument?.id === doc.id ? 'bg-gray-100 dark:bg-gray-800 border-gray-800 dark:border-gray-500' : 'border-transparent hover:bg-gray-50 dark:hover:bg-gray-850'}`}>
                        <div className="flex justify-between items-start">
                           <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex-1 pr-2">{doc.filename}</h3>
                           <StatusIcon status={doc.status} />
              </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                           {new Date(doc.uploadDate).toLocaleDateString()}
                        </p>
                    </button>
                ))}
      </div>
    </div>
  );
};

const DocumentViewer = ({ document, user, onContentGenerated }) => {
    const [activeTab, setActiveTab] = useState('Notes');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [originalContent, setOriginalContent] = useState('');
    
    // The active document now holds its own generated content
    const generatedContent = document?.generated_content || [];

    useEffect(() => {
        if (document) {
            setActiveTab('Notes');
            // Reset original content when document changes
            setOriginalContent('');
        }
    }, [document]);
    
    const handleGenerate = async (contentType) => {
        setIsLoading(true);
        setError('');
        try {
            const newContent = await apiClient.generateContent(user.access, document.id, contentType);
            onContentGenerated(document.id, newContent);
        } catch (err) {
            setError(`Failed to generate ${contentType}.`);
        } finally {
            setIsLoading(false);
        }
    };

    // eslint-disable-next-line no-unused-vars
    const handleViewOriginal = async () => {
        // This is a simplified approach and has security implications in production.
        // It's suitable for local development where the media folder is accessible.
        // A production app would use a secure, authenticated endpoint to serve files.
        if (['txt', 'md'].includes(document.fileType)) {
             // We can't fetch local file paths directly from the browser for security reasons.
             // This is a placeholder to show the concept.
             setOriginalContent("Viewing original content for PDF/DOCX is not supported in this simplified viewer. You can open the file from your local 'media/uploads' directory.");
        } else {
            setOriginalContent("Viewing original content for PDF/DOCX is not supported in this simplified viewer. You can open the file from your local 'media/uploads' directory.");
        }
    };
    
    if (!document) {
        return <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">Select a document to view its content</div>;
    }

    const tabs = ['Notes', 'Summary', 'Quiz', 'Original'];
    const notes = generatedContent.find(c => c.contentType === 'notes');
    const summary = generatedContent.find(c => c.contentType === 'summary');
    const quiz = generatedContent.find(c => c.contentType === 'quiz');

    const renderContent = () => {
        if(isLoading) {
            return <div className="flex justify-center items-center h-full text-gray-500 dark:text-gray-400">{icons.spinner} Generating...</div>;
        }
        if(error) {
            return <p className="text-red-500 text-center">{error}</p>;
        }
        
        switch(activeTab) {
            case 'Notes':
                return notes ? 
                    <div className="prose max-w-none">
                        <ReactMarkdown>{notes.contentData.markdown_text}</ReactMarkdown>
                    </div> : 
                    <p className="text-gray-500 text-center">Initial notes are being generated or have failed.</p>;
            case 'Summary':
                return summary ? 
                    <div className="prose max-w-none">
                        <ReactMarkdown>{summary.contentData.markdown_text}</ReactMarkdown>
                    </div> : 
                    <div className="text-center p-8"><button onClick={() => handleGenerate('summary')} className="bg-gray-800 dark:bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors">Generate Summary</button></div>;
            case 'Quiz':
                 return quiz ?
                    <p className="text-center text-gray-600 dark:text-gray-400">Quiz display not implemented yet.</p> :
                    <div className="text-center p-8"><button onClick={() => handleGenerate('quiz')} className="bg-gray-800 dark:bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors">Generate Quiz</button></div>;
            case 'Original':
                return <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 dark:text-gray-300">{originalContent || "Click button to load original content."}</pre>;
      default:
        return null;
    }
  };

  return (
        <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-gray-850">
            <div className="flex-shrink-0 px-8 pt-6 border-b border-gray-200 dark:border-gray-950 pb-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{document.filename}</h2>
                    <div className="flex items-center space-x-2 p-1 rounded-lg bg-gray-100 dark:bg-gray-800">
                        {tabs.map(tab => (
                            <button key={tab} onClick={() => setActiveTab(tab)}
                                className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors ${activeTab === tab ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'}`}>
                                {tab}
            </button>
          ))}
        </div>
      </div>
            </div>
            <div className="flex-1 p-8 overflow-y-auto">
        {renderContent()}
      </div>
    </div>
  );
};

const SettingsPage = ({ isDarkMode, onToggleDarkMode }) => {
  return (
        <div className="p-8">
            <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">Settings</h1>
            <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <span className="font-medium text-gray-900 dark:text-gray-100">Dark Mode</span>
                <button onClick={onToggleDarkMode} className={`w-14 h-8 rounded-full flex items-center transition-colors p-1 ${isDarkMode ? 'bg-gray-700 justify-end' : 'bg-gray-300 justify-start'}`}>
                    <span className="w-6 h-6 bg-white rounded-full shadow-md transform transition-transform"></span>
              </button>
      </div>
    </div>
  );
};

const ProfilePage = ({ username, onLogout }) => {
  return (
        <div className="p-8">
            <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">Profile</h1>
             <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                <p className="text-gray-900 dark:text-gray-100">Username: <span className="font-semibold">{username}</span></p>
                <button onClick={onLogout} className="mt-6 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors">Logout</button>
      </div>
    </div>
  );
};

const App = () => {
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [activeDocument, setActiveDocument] = useState(null);
  const [activePage, setActivePage] = useState('Documents');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isLoadingApp, setIsLoadingApp] = useState(true);
  // eslint-disable-next-line no-unused-vars
  const [appError, setAppError] = useState('');

  const fetchDocuments = useCallback((token) => {
    setAppError('');
    apiClient.getDocuments(token)
      .then(docs => {
        setDocuments(docs);
        // If there's an active document, update its data in the list
        setActiveDocument(prevActiveDoc => {
          if (prevActiveDoc) {
            const updatedActiveDoc = docs.find(d => d.id === prevActiveDoc.id);
            return updatedActiveDoc || prevActiveDoc;
          }
          return prevActiveDoc;
        });
      })
      .catch(err => {
        console.error(err);
        setAppError('Failed to load documents.');
        if (err.message.includes("401")) { 
            handleLogout();
        }
      });
  }, []); // No dependencies - use functional updates instead

  // Hook to poll for document status updates
  useEffect(() => {
    if (!user || activePage !== 'Documents') return;

    const processingDocs = documents.some(doc => doc.status === 'processing');
    if (!processingDocs) return;

    const interval = setInterval(() => fetchDocuments(user.access), 5000); 

    return () => clearInterval(interval);
  }, [documents, user, activePage, fetchDocuments]);

  useEffect(() => {
    const darkModeSaved = localStorage.getItem('darkMode') === 'true';
    setIsDarkMode(darkModeSaved);

    const sessionUser = JSON.parse(localStorage.getItem('userSession'));
    if (sessionUser) {
      setUser(sessionUser);
    }
    setIsLoadingApp(false);
  }, []);
  
  useEffect(() => {
    if (user?.access) {
      fetchDocuments(user.access);
    }
  }, [user, fetchDocuments]);
  
  useEffect(() => {
      if (isDarkMode) {
          document.documentElement.classList.add('dark');
          localStorage.setItem('darkMode', 'true');
      } else {
          document.documentElement.classList.remove('dark');
          localStorage.setItem('darkMode', 'false');
      }
  }, [isDarkMode]);

  const handleLogin = (userData, rememberMe) => {
    if (rememberMe) {
        localStorage.setItem('userSession', JSON.stringify(userData));
    }
    setUser(userData);
  };

  const handleLogout = () => {
      localStorage.removeItem('userSession');
    setUser(null);
      setDocuments([]);
      setActiveDocument(null);
  };
  
  const handleUpload = async (file) => {
    try {
        const newDoc = await apiClient.uploadDocument(user.access, file);
        setDocuments(prevDocs => [newDoc, ...prevDocs]);
    } catch (error) {
        console.error("Upload failed:", error);
        alert("Upload failed. Please try again.");
    }
  };

  const handleContentGenerated = (docId, newContent) => {
    // This function updates the state to reflect newly generated content
    const updateDocs = (prevDocs) => prevDocs.map(doc => {
        if (doc.id === docId) {
            const newGeneratedContent = [...(doc.generated_content || []), newContent];
            // Also update active document if it's the one
            if(activeDocument?.id === docId) {
                setActiveDocument(prevActive => ({...prevActive, generated_content: newGeneratedContent}));
            }
            return { ...doc, generated_content: newGeneratedContent };
        }
        return doc;
    });
    setDocuments(updateDocs);
  };
  
  if (isLoadingApp) {
      return <div className="h-screen w-screen flex items-center justify-center bg-gray-100 dark:bg-gray-850"><div className="text-gray-500 dark:text-gray-400">{icons.spinner}</div></div>;
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const renderMainContent = () => {
      switch(activePage) {
          case 'Documents':
  return (
                  <div className="flex h-full bg-white dark:bg-gray-850">
                <DocumentList
                  documents={documents}
                        activeDocument={activeDocument} 
                        onSelectDocument={setActiveDocument}
                        onUpload={handleUpload}
                />
                <DocumentViewer
                        document={activeDocument} 
                        user={user} 
                        onContentGenerated={handleContentGenerated} 
                    />
                  </div>
              );
          case 'Settings':
              return <SettingsPage isDarkMode={isDarkMode} onToggleDarkMode={() => setIsDarkMode(!isDarkMode)} />;
          case 'Profile':
              return <ProfilePage username={user.username} onLogout={handleLogout} />;
          default:
              return null;
      }
  };

  return (
    <div className={`flex h-screen font-sans text-gray-900 bg-gray-100 dark:bg-gray-950 transition-colors`}>
        <Sidebar activePage={activePage} setActivePage={setActivePage} />
        <main className="flex-1 flex flex-col">
            <Header 
                username={user.username} 
                onLogout={handleLogout}
                isDarkMode={isDarkMode}
                onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
                onSearch={(query) => apiClient.searchDocuments(user.access, query).then(setDocuments)}
              />
            <div className="flex-1 overflow-hidden p-4 bg-gray-50 dark:bg-gray-950">
                <div className="h-full w-full bg-white dark:bg-gray-850 rounded-xl shadow-sm border border-gray-200 dark:border-gray-950 overflow-hidden">
                    {renderMainContent()}
          </div>
        </div>
        </main>
    </div>
  );
};

export default App;

