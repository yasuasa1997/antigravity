import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { Search, Plus, Trash2, RefreshCw, ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';

const App = () => {
    const [stocks, setStocks] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState([]);
    const [selectedStock, setSelectedStock] = useState(null);

    useEffect(() => {
        fetchStocks();
        const interval = setInterval(fetchStocks, 15000);
        return () => clearInterval(interval);
    }, []);

    const fetchStocks = async () => {
        try {
            const response = await axios.get('/api/stocks');
            setStocks(response.data);
        } catch (error) {
            console.error('Failed to fetch stocks', error);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery) return;
        setLoading(true);
        try {
            const response = await axios.get(`/api/search?q=${searchQuery}`);
            setSearchResults(response.data);
        } catch (error) {
            console.error('Search failed', error);
        } finally {
            setLoading(false);
        }
    };

    const addStock = async (symbol) => {
        try {
            await axios.post(`/api/stocks?symbol=${symbol}`);
            setSearchQuery('');
            setSearchResults([]);
            fetchStocks();
        } catch (error) {
            console.error('Failed to add stock', error);
        }
    };

    const removeStock = async (symbol) => {
        try {
            await axios.delete(`/api/stocks/${symbol}`);
            fetchStocks();
            if (selectedStock === symbol) {
                setSelectedStock(null);
                setHistory([]);
            }
        } catch (error) {
            console.error('Failed to remove stock', error);
        }
    };

    const showHistory = async (symbol) => {
        setSelectedStock(symbol);
        try {
            const response = await axios.get(`/api/stocks/${symbol}/history`);
            setHistory(response.data);
        } catch (error) {
            console.error('Failed to fetch history', error);
        }
    };

    return (
        <div className="dashboard-container">
            <header>
                <h1>Stock Dashboard</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <RefreshCw size={18} className="spin-on-update" />
                    <span>Real-time Updates</span>
                </div>
            </header>

            <main>
                <div className="metrics-grid">
                    {stocks.map((stock) => (
                        <div
                            key={stock.symbol}
                            className={`glass-card price-card ${selectedStock === stock.symbol ? 'selected' : ''}`}
                            onClick={() => showHistory(stock.symbol)}
                        >
                            <div className="symbol">{stock.symbol}</div>
                            <div className="name">{stock.name}</div>
                            <div className="current-price">
                                {stock.price ? stock.price.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '---'}
                            </div>
                            <div className="delta flat">
                                Last updated: {stock.timestamp ? new Date(stock.timestamp).toLocaleTimeString() : 'N/A'}
                            </div>
                            <button
                                className="remove-btn"
                                onClick={(e) => { e.stopPropagation(); removeStock(stock.symbol); }}
                                style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', padding: '0.2rem' }}
                            >
                                <Trash2 size={16} color="#888" />
                            </button>
                        </div>
                    ))}
                </div>

                <div className="chart-section">
                    <div className="glass-card chart-container">
                        <h3>{selectedStock ? `${selectedStock} Price History` : 'Select a stock to view history'}</h3>
                        {history.length > 0 ? (
                            <ResponsiveContainer width="100%" height={400}>
                                <LineChart data={history}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                    <XAxis
                                        dataKey="timestamp"
                                        hide
                                    />
                                    <YAxis domain={['auto', 'auto']} stroke="#888" />
                                    <Tooltip
                                        contentStyle={{ background: '#1a1a20', border: '1px solid #333' }}
                                        labelFormatter={(label) => new Date(label).toLocaleString()}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="price"
                                        stroke="#007aff"
                                        strokeWidth={3}
                                        dot={false}
                                        animationDuration={500}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
                                <TrendingUp size={48} style={{ opacity: 0.2 }} />
                            </div>
                        )}
                    </div>

                    <div className="sidebar-tools">
                        <div className="glass-card search-container">
                            <h3>Add New Ticker</h3>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <input
                                    type="text"
                                    placeholder="Ticker or Company Name..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                    style={{ flex: 1 }}
                                />
                                <button onClick={handleSearch}>
                                    <Search size={18} />
                                </button>
                            </div>

                            {loading && <div style={{ textAlign: 'center' }}>Searching...</div>}

                            <div className="search-results">
                                {searchResults.map((result) => (
                                    <div key={result.symbol} className="search-item" onClick={() => addStock(result.symbol)}>
                                        <div>
                                            <div style={{ fontWeight: 600 }}>{result.symbol}</div>
                                            <div style={{ fontSize: '0.8rem', color: '#888' }}>{result.name}</div>
                                        </div>
                                        <Plus size={18} color="#007aff" />
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="glass-card">
                            <h3>Current Portfolio</h3>
                            <div className="history-list">
                                {stocks.map(s => (
                                    <div key={s.symbol} className="history-item">
                                        <span>{s.symbol}</span>
                                        <a
                                            href={s.symbol.endsWith('.T') ? `https://finance.yahoo.co.jp/quote/${s.symbol}` : `https://finance.yahoo.com/quote/${s.symbol}`}
                                            target="_blank"
                                            rel="noreferrer"
                                        >
                                            <ExternalLink size={14} />
                                        </a>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <style>{`
        .selected {
          border-color: #007aff !important;
          background: rgba(0, 122, 255, 0.05) !important;
        }
        .remove-btn:hover svg {
          color: #ff3b30 !important;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin-on-update {
          color: #888;
        }
      `}</style>
        </div>
    );
};

export default App;
