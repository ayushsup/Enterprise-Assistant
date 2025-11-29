import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';
import { 
  LayoutDashboard, UploadCloud, Database, FileText, 
  MessageSquare, BarChart3, ChevronRight, Send, Loader2, 
  Zap, Pin, Trash2, Download, Activity, Table, 
  CheckCircle, RefreshCw, User, LogOut, Quote, CheckSquare, Lightbulb
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { SignedIn, SignedOut, SignInButton, UserButton, useUser } from "@clerk/clerk-react";

const api = axios.create({ baseURL: '/api' });

// --- UTILS ---
const generateSessionId = () => 'sess_' + Math.random().toString(36).substr(2, 9);

// --- COMPONENTS ---

const KpiCard = ({ title, value, icon: Icon }) => (
  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="kpi-card">
    <div>
      <p className="text-mid" style={{fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase'}}>{title}</p>
      <h3 style={{fontSize: '1.5rem', margin: '0.5rem 0 0 0'}}>{value}</h3>
    </div>
    <div style={{padding: '0.75rem', background: '#eff6ff', borderRadius: '0.5rem', color: '#2563eb'}}>
      <Icon size={24} />
    </div>
  </motion.div>
);

// 1. DASHBOARD VIEW
const DashboardView = ({ session }) => {
    const [pins, setPins] = useState([]);
    
    useEffect(() => {
        if(session.id) {
            api.get(`/analytics/dashboard/${session.id}`)
               .then(res => setPins(res.data))
               .catch(err => console.log("No pins yet"));
        }
    }, [session.id]);

    const deletePin = async (id) => {
        await api.delete(`/analytics/dashboard/${id}`);
        setPins(pins.filter(p => p.id !== id));
    };

    return (
        <div className="fade-in">
            <header className="dashboard-header">
                <h2>Executive Dashboard</h2>
                <p>Overview of your saved insights and key metrics.</p>
            </header>

            {session.meta && (
                <div className="kpi-grid">
                    <KpiCard title="Total Records" value={session.meta.total_rows.toLocaleString()} icon={Database} />
                    <KpiCard title="Features" value={session.meta.total_columns} icon={Table} />
                    <KpiCard title="Numeric Fields" value={session.meta.numeric_cols.length} icon={Activity} />
                    <KpiCard title="Data Quality" value={`${100 - Math.round((session.meta.total_rows * 0.01))} %`} icon={Zap} />
                </div>
            )}

            <div className="pin-grid">
                {pins.length === 0 ? (
                    <div className="chart-card" style={{gridColumn: '1 / -1', alignItems: 'center', justifyContent: 'center', borderStyle: 'dashed'}}>
                        <div style={{background: '#f1f5f9', padding: '1rem', borderRadius: '50%', marginBottom: '1rem'}}>
                            <Pin size={24} color="#94a3b8" />
                        </div>
                        <h3>Your Pinboard is Empty</h3>
                        <p style={{color: '#64748b'}}>Go to Visualization or AI Assistant to pin charts and insights.</p>
                    </div>
                ) : (
                    pins.map(pin => (
                        <div key={pin.id} className="chart-card" style={{height: pin.chart_type === 'text' ? 'auto' : '450px', minHeight: pin.chart_type === 'text' ? '200px' : '450px'}}>
                            <div className="chart-header">
                                <strong style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                                    {pin.chart_type === 'text' ? <Quote size={16} color="#3b82f6"/> : <BarChart3 size={16} color="#a855f7"/>}
                                    {pin.title}
                                </strong>
                                <button onClick={() => deletePin(pin.id)} style={{border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8'}}><Trash2 size={16}/></button>
                            </div>
                            
                            <div className="chart-wrapper" style={{overflow: 'auto'}}>
                                {pin.chart_type === 'text' ? (
                                    <div style={{padding: '1rem', background: '#f8fafc', borderRadius: '0.5rem', fontSize: '0.95rem', lineHeight: '1.6', color: '#334155', whiteSpace: 'pre-wrap', border: '1px solid #e2e8f0'}}>
                                        {pin.chart_config.text}
                                    </div>
                                ) : (
                                    <Plot 
                                        data={pin.chart_config.data} 
                                        layout={{...pin.chart_config.layout, autosize: true, margin: {l:40, r:20, t:20, b:40}}} 
                                        useResizeHandler={true} 
                                        style={{width: "100%", height: "100%"}} 
                                        config={{displayModeBar: false, responsive: true}} 
                                    />
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

// 2. DATA INGESTION VIEWS
const CsvUploadView = ({ session, onUpload }) => {
    const [loading, setLoading] = useState(false);
    
    if (session.meta) {
        return (
            <div className="card-centered">
                <div style={{margin: '0 auto 1.5rem auto', width: '60px', height: '60px', background: '#dcfce7', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <CheckCircle size={32} color="#16a34a" />
                </div>
                <h2>Data Active</h2>
                <p style={{color: '#64748b', marginBottom: '2rem'}}>You are currently analyzing <strong>{session.meta.filename}</strong>.</p>
                <button onClick={() => onUpload(null)} className="btn-primary" style={{background: '#fff', color: '#64748b', border: '1px solid #e2e8f0', justifyContent: 'center'}}>
                    <RefreshCw size={18} /> Upload Different File
                </button>
            </div>
        );
    }

    const handleFile = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await api.post('/data/upload', formData);
            onUpload(res.data); 
        } catch (err) { alert("Upload failed"); } 
        finally { setLoading(false); }
    };

    return (
        <div className="card-centered">
            <div style={{margin: '0 auto 1.5rem auto', width: '60px', height: '60px', background: '#eff6ff', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <UploadCloud size={32} color="#2563eb" />
            </div>
            <h2>Upload Structured Data</h2>
            <p style={{color: '#64748b', marginBottom: '2rem'}}>Upload CSV or Excel files to enable analysis.</p>
            
            <label className="upload-zone">
                {loading ? <Loader2 className="spin" size={32} color="#2563eb" /> : <FileText size={32} color="#94a3b8" />}
                <span style={{fontWeight: 600, color: '#2563eb', marginTop: '1rem'}}>Click to browse</span>
                <span style={{fontSize: '0.8rem', color: '#94a3b8'}}>CSV, XLSX (Max 200MB)</span>
                <input type="file" className="hidden" onChange={handleFile} accept=".csv,.xlsx" />
            </label>
        </div>
    );
};

const SqlConnectView = ({ session, onConnect, onDisconnect }) => {
    const [connStr, setConnStr] = useState("");
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("idle"); 

    if (session.sqlConnected) {
        return (
            <div className="card-centered">
                <div style={{margin: '0 auto 1.5rem auto', width: '60px', height: '60px', background: '#dcfce7', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <Database size={32} color="#16a34a" />
                </div>
                <h2>Database Connected</h2>
                <p style={{color: '#64748b', marginBottom: '2rem'}}>SQL Agent is active and ready for queries.</p>
                <button onClick={onDisconnect} className="btn-danger" style={{justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                    Disconnect
                </button>
            </div>
        );
    }

    const connect = async () => {
        setLoading(true);
        try {
            await api.post('/analytics/sql/connect', { session_id: session.id, connection_string: connStr });
            setStatus("success");
            onConnect(); 
        } catch { setStatus("error"); }
        setLoading(false);
    };

    return (
        <div className="card-centered" style={{textAlign: 'left'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem'}}>
                <div style={{padding: '0.75rem', background: '#f3e8ff', borderRadius: '0.5rem', color: '#9333ea'}}><Database size={24}/></div>
                <div>
                    <h2 style={{margin: 0, fontSize: '1.2rem'}}>Connect Database</h2>
                    <p style={{margin: 0, fontSize: '0.9rem', color: '#64748b'}}>PostgreSQL or MySQL.</p>
                </div>
            </div>
            
            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                <div>
                    <label style={{display: 'block', fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.5rem'}}>Connection String</label>
                    <input className="input-field" style={{width: '100%'}} placeholder="postgresql://user:password@localhost:5432/mydb" value={connStr} onChange={e => setConnStr(e.target.value)} />
                </div>
                
                <button onClick={connect} disabled={loading} className="btn-primary" style={{justifyContent: 'center', background: '#9333ea'}}>
                    {loading ? "Connecting..." : "Establish Connection"}
                </button>

                {status === "error" && <div style={{padding: '0.75rem', background: '#fee2e2', color: '#b91c1c', borderRadius: '0.5rem', textAlign: 'center'}}>❌ Connection failed.</div>}
            </div>
        </div>
    );
};

const PdfUploadView = ({ session, onUpload }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);

    if (session.pdfUploaded) {
        return (
            <div className="card-centered">
                <div style={{margin: '0 auto 1.5rem auto', width: '60px', height: '60px', background: '#dcfce7', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <FileText size={32} color="#16a34a" />
                </div>
                <h2>Document Indexed</h2>
                <p style={{color: '#64748b', marginBottom: '2rem'}}>The Knowledge Base is ready for questions.</p>
                <button onClick={() => onUpload(false)} className="btn-primary" style={{background: '#fff', color: '#64748b', border: '1px solid #e2e8f0', justifyContent: 'center'}}>
                    <RefreshCw size={18} /> Upload New Document
                </button>
            </div>
        );
    }

    const handleUpload = async () => {
        if(!file) return;
        setUploading(true);
        const formData = new FormData(); formData.append('file', file);
        try {
            await api.post(`/analytics/rag/upload?session_id=${session.id}`, formData);
            onUpload(true); 
        } catch { alert("Error uploading file"); }
        setUploading(false);
    };

    return (
        <div className="card-centered">
            <div style={{margin: '0 auto 1.5rem auto', width: '60px', height: '60px', background: '#ffedd5', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <FileText size={32} color="#ea580c" />
            </div>
            <h2>Knowledge Base Upload</h2>
            <p style={{color: '#64748b', marginBottom: '2rem'}}>Upload PDF or PowerPoint reports to chat with them.</p>
            
            <div className="upload-zone" style={{borderColor: '#fdba74', background: '#fff7ed'}}>
                <input type="file" onChange={e => setFile(e.target.files[0])} accept=".pdf,.pptx,.ppt" style={{marginBottom: '1rem'}} />
                <button onClick={handleUpload} disabled={uploading || !file} className="btn-primary" style={{background: '#ea580c'}}>
                    {uploading ? "Indexing..." : "Upload & Index"}
                </button>
            </div>
        </div>
    );
};

// 3. UNIFIED AI ASSISTANT
const UnifiedChatView = ({ session, chatHistories, onUpdateHistory, onCacheSuggestions }) => {
    const [mode, setMode] = useState('csv'); 
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [suggestions, setSuggestions] = useState(session.suggestions || []); 
    const scrollRef = useRef(null);
    
    const [isSelectionMode, setIsSelectionMode] = useState(false);
    const [selectedIndices, setSelectedIndices] = useState(new Set());

    // --- SMART SUGGESTIONS HANDLER (Caching Logic) ---
    const fetchAndCacheSuggestions = async (force = false) => {
        
        let endpoint = '';
        let canFetch = false;
        
        // Determine the correct endpoint based on the active mode
        if (mode === 'csv' && session.meta) {
            if (force || !session.suggestions || session.suggestions.length === 0) {
                endpoint = `/analytics/suggestions/csv/${session.id}`;
                canFetch = true;
            }
        } else if (mode === 'sql' && session.sqlConnected) {
            endpoint = `/analytics/suggestions/sql/${session.id}`;
            canFetch = true;
        } else if (mode === 'pdf' && session.pdfUploaded) {
            endpoint = `/analytics/suggestions/rag/${session.id}`;
            canFetch = true;
        } else {
            setSuggestions([]); // Clear if mode is not active
            return;
        }

        // If cache exists for CSV and we aren't forcing, use cache
        if (!force && mode === 'csv' && session.suggestions && session.suggestions.length > 0) {
             setSuggestions(session.suggestions);
             return;
        }

        if (canFetch) {
            setLoading(true);
            try {
                const res = await api.get(endpoint);
                const newSuggestions = res.data.suggestions || [];
                setSuggestions(newSuggestions);
                onCacheSuggestions(newSuggestions); // Save to App state
            } catch(e) { 
                console.error(`Failed to fetch ${mode} suggestions:`, e);
                setSuggestions([`Error loading ${mode} suggestions.`]);
                onCacheSuggestions(null); 
            } finally {
                setLoading(false);
            }
        }
    };

    // 1. Initial Load / Tab Switch Effect
    useEffect(() => {
        fetchAndCacheSuggestions(false);
    }, [session.id, mode, session.meta, session.sqlConnected, session.pdfUploaded]);

    // 2. UI/Scroll Logic
    useEffect(() => {
        if (session.sqlConnected && !session.meta && mode === 'csv') setMode('sql');
        if (session.pdfUploaded && !session.meta && !session.sqlConnected && mode === 'csv') setMode('pdf');
    }, [session.sqlConnected, session.pdfUploaded, session.meta]);

    useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatHistories[mode]]);

    const sendMessage = async (text = input) => {
        if (!text.trim() || loading) return;
        
        const userMsg = { role: 'user', content: text };
        onUpdateHistory(mode, userMsg);
        setInput("");
        setLoading(true);

        const aiMsgPlaceholder = { role: 'assistant', content: "" };
        onUpdateHistory(mode, aiMsgPlaceholder);

        let endpoint = '/chat/query';
        if (mode === 'sql') endpoint = '/analytics/sql/query';
        if (mode === 'pdf') endpoint = '/analytics/rag/query';

        try {
            const response = await fetch(`/api${endpoint}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: session.id, query: userMsg.content })
            });

            if (!response.body) throw new Error("No stream");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                if (mode === 'csv') { 
                    aiText += chunk; 
                    onUpdateHistory(mode, { role: 'assistant', content: aiText }, true); 
                } else { 
                    aiText += chunk; 
                }
            }
            
            if (mode !== 'csv') {
                try { 
                    const jsonRes = JSON.parse(aiText); 
                    onUpdateHistory(mode, jsonRes, true); 
                } catch (e) { 
                    onUpdateHistory(mode, { role: 'assistant', content: aiText }, true); 
                }
            }

        } catch (err) {
            onUpdateHistory(mode, { role: 'assistant', content: "Error: Connection failed." }, true);
        } finally {
            setLoading(false);
        }
    };

    const pinMessage = async (content, type = 'text') => {
        try {
            const title = typeof content === 'string' 
                ? (content.split('\n')[0].substring(0, 30) + "...") 
                : "Saved Chart";

            await api.post('/analytics/dashboard/pin', {
                session_id: session.id, title: title, chart_type: type, 
                chart_config: type === 'text' ? { text: content } : content 
            });
            alert("Pinned to Dashboard!");
        } catch (e) { alert("Failed to pin"); }
    };

    const toggleSelection = (index) => {
        const newSet = new Set(selectedIndices);
        if (newSet.has(index)) newSet.delete(index);
        else newSet.add(index);
        setSelectedIndices(newSet);
    };

    const handleExport = async () => {
        if (selectedIndices.size === 0) return;
        const activeMessages = chatHistories[mode] || [];
        const messagesToExport = activeMessages.filter((_, i) => selectedIndices.has(i));
        try {
            const response = await api.post('/analytics/report/chat', {
                session_id: session.id, messages: messagesToExport
            }, { responseType: 'blob' });
            
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url; link.setAttribute('download', 'Selected_Insights.pdf');
            document.body.appendChild(link); link.click();
            
            setIsSelectionMode(false); setSelectedIndices(new Set());
        } catch (e) { alert("Export failed"); }
    };

    const SqlChartRenderer = ({ data }) => {
        try {
            const chartData = typeof data === 'string' ? JSON.parse(data) : data;
            if (!chartData.x || !chartData.y) return <div className="p-2 text-red-500">Invalid Chart Data</div>;
            return (
                <div style={{marginTop: '0.5rem'}}>
                    <div style={{height: '300px', width: '100%', background: 'white', borderRadius: '0.5rem', border: '1px solid #e2e8f0', padding: '0.5rem'}}>
                        <Plot data={[{ x: chartData.x, y: chartData.y, type: chartData.chart_type || 'bar', marker: { color: '#2563eb' } }]} layout={{ title: chartData.title, autosize: true, margin: { l: 40, r: 10, t: 30, b: 40 } }} useResizeHandler={true} style={{ width: "100%", height: "100%" }} config={{ displayModeBar: false }} />
                    </div>
                    <button onClick={() => pinMessage(chartData, 'bar')} style={{marginTop: '0.5rem', fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', border: 'none', background: 'none'}}><Pin size={14} /> Pin Chart</button>
                </div>
            );
        } catch (e) { return <div style={{whiteSpace: 'pre-wrap'}}>{typeof data === 'string' ? data : JSON.stringify(data)}</div>; }
    };

    const activeMessages = chatHistories[mode] || [];

    return (
        <div className="chat-layout">
            <div className="chat-context">
                <h3 style={{fontSize: '1rem', fontWeight: 700, marginBottom: '1rem'}}>Context</h3>
                <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                    <button onClick={() => setMode('csv')} disabled={!session.meta} className={`context-btn ${mode === 'csv' ? 'active' : ''} ${!session.meta ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        <Table size={18} /> CSV Data
                    </button>
                    <button onClick={() => setMode('sql')} disabled={!session.sqlConnected} className={`context-btn ${mode === 'sql' ? 'active' : ''} ${!session.sqlConnected ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        <Database size={18} /> SQL Database
                    </button>
                    <button onClick={() => setMode('pdf')} disabled={!session.pdfUploaded} className={`context-btn ${mode === 'pdf' ? 'active' : ''} ${!session.pdfUploaded ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        <FileText size={18} /> Documents
                    </button>
                </div>
                
                {/* --- RESTORED: SUGGESTIONS UI --- */}
                {((mode === 'csv' && session.meta) || (mode === 'sql' && session.sqlConnected) || (mode === 'pdf' && session.pdfUploaded)) && (
                    <div style={{marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0'}}>
                        <h4 style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                             <Lightbulb size={14} color="#f59e0b" /> Smart Suggestions
                             {loading && <Loader2 size={14} className="spin" color="#f59e0b" />}

                             {/* ADDED: Manual Refresh Button */}
                             {!loading && (
                                <button 
                                    onClick={() => fetchAndCacheSuggestions(true)} 
                                    title="Regenerate suggestions"
                                    style={{border: 'none', background: 'none', padding: '0 0 0 0.5rem', cursor: 'pointer'}}
                                >
                                    <RefreshCw size={14} color="#64748b" />
                                </button>
                             )}
                             
                        </h4>
                        <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                            {suggestions.length > 0 ? suggestions.map((s, i) => (
                                <button 
                                    key={i} 
                                    onClick={() => sendMessage(s)} 
                                    style={{textAlign: 'left', fontSize: '0.8rem', padding: '0.6rem', background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '0.5rem', color: '#0284c7', cursor: 'pointer', transition: 'background 0.2s'}}
                                    className="hover:bg-blue-100"
                                >
                                    {s}
                                </button>
                            )) : <span style={{fontSize: '0.8rem', color: '#94a3b8'}}>Thinking...</span>}
                        </div>
                    </div>
                )}

                {/* --- EXPORT SECTION --- */}
                <div style={{marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0'}}>
                    <h4 style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b', marginBottom: '0.5rem'}}>Actions</h4>
                    {!isSelectionMode ? (
                        <button onClick={() => setIsSelectionMode(true)} className="btn-primary" style={{width: '100%', fontSize: '0.8rem', justifyContent: 'center', background: '#fff', color: '#0f172a', border: '1px solid #cbd5e1'}}>
                            <CheckSquare size={14}/> Select & Export
                        </button>
                    ) : (
                        <div style={{display: 'flex', gap: '0.5rem', flexDirection: 'column'}}>
                            <button onClick={handleExport} disabled={selectedIndices.size === 0} className="btn-primary" style={{width: '100%', fontSize: '0.8rem', justifyContent: 'center'}}>
                                <Download size={14}/> Download PDF ({selectedIndices.size})
                            </button>
                            <button onClick={() => { setIsSelectionMode(false); setSelectedIndices(new Set()); }} className="btn-danger" style={{width: '100%', fontSize: '0.8rem', padding: '0.5rem'}}>
                                Cancel
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="chat-window">
                <div className="chat-messages">
                    {activeMessages.length === 0 && (
                        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8'}}>
                            <MessageSquare size={48} style={{marginBottom: '1rem', opacity: 0.3}} />
                            <p>Chatting with <strong>{mode.toUpperCase()}</strong> Source</p>
                        </div>
                    )}
                    {activeMessages.map((m, i) => (
                        <div key={i} style={{display: 'flex', gap: '0.5rem', marginBottom: '1rem', alignItems: 'start'}}>
                            
                            {/* CHECKBOX (Visible only in Selection Mode) */}
                            {isSelectionMode && (
                                <input 
                                    type="checkbox" 
                                    checked={selectedIndices.has(i)} 
                                    onChange={() => toggleSelection(i)}
                                    style={{marginTop: '1.2rem', transform: 'scale(1.2)', cursor: 'pointer'}}
                                />
                            )}

                            <div className={`message ${m.role}`} style={{flex: 1, position: 'relative'}}>
                                {/* Pin Button for Assistant Messages */}
                                {m.role === 'assistant' && !isSelectionMode && !loading && (
                                    <button 
                                        onClick={() => pinMessage(m.content, 'text')}
                                        style={{position: 'absolute', top: '5px', right: '5px', opacity: 0.5, cursor: 'pointer', border: 'none', background: 'none'}}
                                        title="Pin to Dashboard"
                                    >
                                        <Pin size={14} />
                                    </button>
                                )}

                                {m.role === 'assistant' ? (
                                    (m.content && (m.content.includes('"chart_type"') || m.content.trim().startsWith('{'))) ? 
                                        <SqlChartRenderer data={m.content} /> :
                                        <div dangerouslySetInnerHTML={{ __html: m.content ? m.content.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') : '' }} />
                                ) : m.content}
                            </div>
                        </div>
                    ))}
                    {loading && <div className="message assistant"><Loader2 className="spin" size={16} /> Thinking...</div>}
                    <div ref={scrollRef} />
                </div>
                <div className="chat-input-container" style={{opacity: isSelectionMode ? 0.5 : 1, pointerEvents: isSelectionMode ? 'none' : 'auto'}}>
                    <input className="input-field" placeholder={`Ask ${mode}...`} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} disabled={loading} />
                    <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn-primary"><Send size={18} /></button>
                </div>
            </div>
        </div>
    );
};

// 4. VISUALIZATION VIEW
const VisualizationView = ({ session }) => {
    const [tables, setTables] = useState([]);
    const [selectedTable, setSelectedTable] = useState("");
    const [columns, setColumns] = useState([]);
    const [numericCols, setNumericCols] = useState([]);
    const [config, setConfig] = useState({ x_axis: "", y_axis: "", chart_type: "Scatter Plot", color_by: "None" });
    const [plotData, setPlotData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const loadSource = async () => {
            if (session.meta) {
                setColumns(session.meta.columns); setNumericCols(session.meta.numeric_cols);
                setConfig(prev => ({ ...prev, x_axis: session.meta.columns[0], y_axis: session.meta.numeric_cols[0] }));
            } else if (session.sqlConnected) {
                try { const res = await api.get(`/analytics/sql/tables/${session.id}`); if (res.data.tables && res.data.tables.length > 0) { setTables(res.data.tables); setSelectedTable(res.data.tables[0]); } } catch (e) {}
            }
        }; loadSource();
    }, [session.meta, session.sqlConnected, session.id]);

    useEffect(() => {
        if (selectedTable && session.sqlConnected && !session.meta) {
            const fetchCols = async () => {
                try { const res = await api.get(`/analytics/sql/columns/${session.id}/${selectedTable}`); setColumns(res.data.columns); setNumericCols(res.data.numeric_cols); setConfig(prev => ({ ...prev, x_axis: res.data.columns[0] || "", y_axis: res.data.numeric_cols[0] || "" })); } catch(e) { console.error("Error fetching columns"); }
            }; fetchCols();
        }
    }, [selectedTable, session.sqlConnected, session.meta, session.id]);

    if (!session.meta && !session.sqlConnected) return <div className="card-centered" style={{color: '#94a3b8'}}><BarChart3 size={48} /><p>No Data Available. Upload a CSV or Connect to SQL.</p></div>;

    const generatePlot = async () => {
        setLoading(true); try {
            let payload = { 
                session_id: session.id, 
                chart_type: config.chart_type, 
                x_axis: config.x_axis, 
                y_axis: config.y_axis,
                color_by: config.color_by === "None" ? null : config.color_by
            };

            if (session.meta) {
                const res = await api.post('/analytics/visualize', payload); setPlotData(res.data);
            } else {
                const query = `Generate a ${config.chart_type} of ${config.y_axis} vs ${config.x_axis} from table ${selectedTable}, coloring the segments by the ${config.color_by} column.`;
                const res = await api.post('/analytics/sql/query', { session_id: session.id, query });
                try { const chartJson = JSON.parse(res.data.content); setPlotData({ data: [{ x: chartJson.x, y: chartJson.y, type: chartJson.chart_type || 'bar', marker: { color: '#2563eb' } }], layout: { title: chartJson.title, xaxis: { title: chartJson.x_label }, yaxis: { title: chartJson.y_label } } }); } catch (e) { alert("AI failed to generate valid chart data."); }
            }
        } catch { alert("Error generating chart"); } finally { setLoading(false); }
    };

    const pinChart = async () => {
        if(!plotData) return;
        await api.post('/analytics/dashboard/pin', { session_id: session.id, title: `${config.chart_type}: ${config.y_axis} vs ${config.x_axis}`, chart_type: config.chart_type, chart_config: plotData }); alert("Pinned!");
    };

    return (
        <div style={{display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem'}}>
            <div style={{background: 'white', padding: '1.5rem', borderRadius: '1rem', border: '1px solid #e2e8f0', height: 'fit-content'}}>
                <h3 style={{margin: '0 0 1rem 0'}}>Configuration</h3>
                <div style={{marginBottom: '1rem', fontSize: '0.75rem', color: session.meta ? '#16a34a' : '#9333ea', fontWeight: 700, textTransform: 'uppercase'}}>Source: {session.meta ? "CSV File" : `SQL Table (${selectedTable || "Connected"})`}</div>
                {session.sqlConnected && !session.meta && <div style={{marginBottom: '1rem'}}><label style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b'}}>Select Table</label><select className="input-field" style={{width: '100%'}} value={selectedTable} onChange={e => setSelectedTable(e.target.value)}>{tables.map(t => <option key={t} value={t}>{t}</option>)}</select></div>}
                <div style={{marginBottom: '1rem'}}><label style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b'}}>Chart Type</label><select className="input-field" style={{width: '100%'}} value={config.chart_type} onChange={e => setConfig({...config, chart_type: e.target.value})}>{["Scatter Plot", "Line Chart", "Bar Chart", "Box Plot", "Histogram"].map(t => <option key={t} value={t}>{t}</option>)}</select></div>
                <div style={{marginBottom: '1rem'}}><label style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b'}}>X Axis</label><select className="input-field" style={{width: '100%'}} value={config.x_axis} onChange={e => setConfig({...config, x_axis: e.target.value})}>{columns.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
                <div style={{marginBottom: '1rem'}}><label style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b'}}>Y Axis</label><select className="input-field" style={{width: '100%'}} value={config.y_axis} onChange={e => setConfig({...config, y_axis: e.target.value})}>{numericCols.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
                
                {/* RESTORED: COLOR BY Dropdown */}
                <div style={{marginBottom: '1rem'}}><label style={{fontSize: '0.8rem', fontWeight: 700, color: '#64748b'}}>Color By (Groups)</label>
                    <select className="input-field" style={{width: '100%'}} value={config.color_by} onChange={e => setConfig({...config, color_by: e.target.value})}>
                        <option value="None">None</option>
                        {columns.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                </div>
                {/* END RESTORED */}
                
                <button onClick={generatePlot} disabled={loading} className="btn-primary" style={{width: '100%', justifyContent: 'center'}}>{loading ? "Loading..." : "Generate"}</button>
            </div>
            <div className="chart-card" style={{height: '500px', position: 'relative'}}>
                {plotData ? (<><button onClick={pinChart} style={{position: 'absolute', top: 10, right: 10, zIndex: 10, background: 'white', border: '1px solid #e2e8f0', padding: '0.5rem', borderRadius: '0.5rem', cursor: 'pointer'}}><Pin size={16}/></button><div className="chart-wrapper"><Plot data={plotData.data} layout={{...plotData.layout, autosize: true, margin: {l:40, r:20, t:20, b:40}}} useResizeHandler={true} style={{width: "100%", height: "100%"}} config={{displayModeBar: false, responsive: true}} /></div></>) : <div style={{height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8'}}>Generate a chart to view</div>}
            </div>
        </div>
    );
};

// --- MAIN APP ---
export default function App() {
  const { isSignedIn, user, isLoaded } = useUser();
  const [activeView, setActiveView] = useState('dashboard'); 
  
  const [session, setSession] = useState(() => {
      const saved = localStorage.getItem('gemchat_session_data');
      return saved ? JSON.parse(saved) : { id: null, meta: null, sqlConnected: false, pdfUploaded: false, suggestions: [] };
  });
  
  const [chatHistories, setChatHistories] = useState({ csv: [], sql: [], pdf: [] });

  useEffect(() => { localStorage.setItem('gemchat_session_data', JSON.stringify(session)); }, [session]);

  const handleUpdateHistory = (mode, message, replaceLast = false) => {
      setChatHistories(prev => {
          const current = prev[mode];
          if (replaceLast && current.length > 0) return { ...prev, [mode]: [...current.slice(0, -1), message] };
          return { ...prev, [mode]: [...current, message] };
      });
  };

  const handleCacheSuggestions = (newSuggestions) => {
      setSession(prev => ({ ...prev, suggestions: newSuggestions }));
  };

  useEffect(() => { if (isSignedIn && user && !session.id) setSession(prev => ({ ...prev, id: user.id })); }, [isSignedIn, user, session.id]);

  const handleCsvUpload = (metaData) => { if (!metaData) setSession(prev => ({ ...prev, meta: null, suggestions: [] })); else { setSession(prev => ({ ...prev, meta: metaData, id: metaData.session_id, suggestions: [] })); setActiveView('dashboard'); } };
  const handleSqlConnect = () => setSession(prev => ({ ...prev, sqlConnected: true }));
  const handlePdfUpload = (status) => setSession(prev => ({ ...prev, pdfUploaded: status }));
  const handleReset = () => { localStorage.removeItem('gemchat_session_data'); setSession({ id: user?.id || generateSessionId(), meta: null, sqlConnected: false, pdfUploaded: false, suggestions: [] }); setChatHistories({ csv: [], sql: [], pdf: [] }); window.location.reload(); };

  // --- FIX: Full Report Download Handler ---
  const handleDownloadFullReport = () => {
      // Determine the active source type
      const activeSource = session.meta ? 'CSV' : (session.sqlConnected ? 'SQL' : (session.pdfUploaded ? 'RAG' : null));
      
      if (!activeSource) {
          alert("Please upload or connect a data source before downloading a report.");
          return;
      }
      
      const sourceId = session.meta ? session.meta.session_id : session.id;
      
      // Use the new multi-source endpoint structure
      window.open(`/api/analytics/report/${activeSource}/${sourceId}`, '_blank');
  };
  // ------------------------------------------

  if (!isLoaded) return <div style={{display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center'}}><Loader2 className="spin" size={48} color="#2563eb"/></div>;
  if (!isSignedIn) return <div style={{display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8fafc'}}><div className="card-centered"><h1>AssistEnterprise</h1><SignInButton mode="modal"><button className="btn-primary">Sign In</button></SignInButton></div></div>;

  const NavItem = ({ id, label, icon: Icon }) => <button onClick={() => setActiveView(id)} className={`nav-item ${activeView === id ? 'active' : ''}`}><Icon size={18} /> {label}</button>;

  return (
    <div className="app-container">
        <aside className="sidebar">
            <div className="sidebar-header"><h1 className="brand-title">EnterpriseAssist</h1><p className="brand-subtitle">Welcome, {user.firstName}</p></div>
            <nav className="nav-menu">
                <NavItem id="dashboard" label="Dashboard" icon={LayoutDashboard} />
                <div className="nav-section-label">Data Sources</div>
                <NavItem id="ingest_csv" label="Upload CSV" icon={Table} />
                <NavItem id="ingest_sql" label="Connect SQL" icon={Database} />
                <NavItem id="ingest_pdf" label="Upload Docs" icon={FileText} />
                <div className="nav-section-label">Analytics</div>
                <NavItem id="chat" label="AI Assistant" icon={MessageSquare} />
                <NavItem id="viz" label="Visualizations" icon={BarChart3} />
            </nav>
            <div className="sidebar-footer">
                <button onClick={handleDownloadFullReport} className="btn-primary" style={{width: '100%', justifyContent: 'center', marginBottom: '1rem'}}><Download size={16} /> Full Data Report</button>
                <button onClick={handleReset} className="btn-danger">Reset Session</button>
                <div style={{marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}><UserButton /><span style={{fontSize: '0.85rem', fontWeight: 600}}>{user.fullName}</span></div>
            </div>
        </aside>
        <main className="main-content">
            <div className="content-wrapper">
                <AnimatePresence mode="wait">
                    <motion.div key={activeView} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
                        {activeView === 'dashboard' && <DashboardView session={session} />}
                        {activeView === 'ingest_csv' && <CsvUploadView session={session} onUpload={handleCsvUpload} />}
                        {activeView === 'ingest_sql' && <SqlConnectView session={session} onConnect={handleSqlConnect} onDisconnect={() => setSession({...session, sqlConnected: false})} />}
                        {activeView === 'ingest_pdf' && <PdfUploadView session={session} onUpload={handlePdfUpload} />}
                        {activeView === 'chat' && <UnifiedChatView session={session} chatHistories={chatHistories} onUpdateHistory={handleUpdateHistory} onCacheSuggestions={handleCacheSuggestions} />}
                        {activeView === 'viz' && <VisualizationView session={session} />}
                    </motion.div>
                </AnimatePresence>
            </div>
        </main>
    </div>
  );
}