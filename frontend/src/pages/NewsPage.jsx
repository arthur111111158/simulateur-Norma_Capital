import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Newspaper, 
  Search, 
  Clock, 
  Globe, 
  TrendingUp, 
  Filter,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

const NewsPage = () => {
  const { news, fetchNews } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('all');
  const [selectedTag, setSelectedTag] = useState('all');
  const [loading, setLoading] = useState(false);

  // Get unique tags from news
  const allTags = [...new Set(news.flatMap(article => article.tags || []))].filter(Boolean);
  
  // Filter news
  const filteredNews = news.filter(article => {
    const matchesSearch = !searchQuery || 
      article.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.description?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTag = selectedTag === 'all' || 
      article.tags?.includes(selectedTag);
    
    return matchesSearch && matchesTag;
  });

  // Handle search
  const handleSearch = async () => {
    setLoading(true);
    await fetchNews(searchQuery || null, selectedCountry !== 'all' ? selectedCountry : null);
    setLoading(false);
  };

  // Refresh news
  const handleRefresh = async () => {
    setLoading(true);
    await fetchNews();
    setLoading(false);
  };

  // Get sentiment color
  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'text-emerald-500';
      case 'negative': return 'text-red-500';
      default: return 'text-zinc-400';
    }
  };

  // Countries for filter
  const countries = [
    { value: 'all', label: 'All Countries' },
    { value: 'us', label: 'United States' },
    { value: 'gb', label: 'United Kingdom' },
    { value: 'de', label: 'Germany' },
    { value: 'fr', label: 'France' },
    { value: 'jp', label: 'Japan' },
    { value: 'cn', label: 'China' },
    { value: 'au', label: 'Australia' },
  ];

  return (
    <div className="space-y-4" data-testid="news-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500/20 rounded-sm flex items-center justify-center">
                <Newspaper className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">News Terminal</h1>
                <p className="text-sm text-zinc-500">Real-time global news with asset tagging</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="live-indicator text-zinc-400 px-3 py-1 bg-zinc-900 rounded-sm">
                <span className="text-emerald-500">LIVE FEED</span>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleRefresh}
                disabled={loading}
                data-testid="refresh-news-btn"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card className="nexus-card">
        <CardContent className="p-3">
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                type="text"
                placeholder="Search news..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-9 bg-zinc-900 border-zinc-800"
                data-testid="news-search-input"
              />
            </div>
            
            <Select value={selectedCountry} onValueChange={setSelectedCountry}>
              <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800" data-testid="country-select">
                <Globe className="w-4 h-4 mr-2 text-zinc-500" />
                <SelectValue placeholder="Country" />
              </SelectTrigger>
              <SelectContent>
                {countries.map((country) => (
                  <SelectItem key={country.value} value={country.value}>
                    {country.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedTag} onValueChange={setSelectedTag}>
              <SelectTrigger className="w-[150px] bg-zinc-900 border-zinc-800" data-testid="tag-select">
                <Filter className="w-4 h-4 mr-2 text-zinc-500" />
                <SelectValue placeholder="Tag" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tags</SelectItem>
                {allTags.map((tag) => (
                  <SelectItem key={tag} value={tag}>{tag}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button onClick={handleSearch} disabled={loading} data-testid="search-btn">
              <Search className="w-4 h-4 mr-2" />
              Search
            </Button>
          </div>

          {/* Tag Pills */}
          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-zinc-800">
              <span className="text-xs text-zinc-500 mr-2">Quick filters:</span>
              {['MACRO', 'OIL', 'GOLD', 'TECH', 'AAPL', 'MSFT'].map((tag) => (
                <Badge 
                  key={tag}
                  variant={selectedTag === tag ? 'default' : 'outline'}
                  className={`cursor-pointer rounded-none text-xs ${selectedTag === tag ? 'bg-orange-500' : 'hover:bg-zinc-800'}`}
                  onClick={() => setSelectedTag(selectedTag === tag ? 'all' : tag)}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* News Feed */}
      <div className="grid grid-cols-12 gap-4">
        {/* Main Feed */}
        <div className="col-span-8">
          <Card className="nexus-card">
            <CardHeader className="card-header-terminal">
              <CardTitle className="card-header-title">
                News Feed ({filteredNews.length} articles)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[calc(100vh-350px)]">
                {filteredNews.map((article, i) => (
                  <div 
                    key={article.id || i}
                    className="p-4 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer transition-colors duration-75"
                    onClick={() => window.open(article.url, '_blank')}
                    data-testid={`news-article-${i}`}
                  >
                    <div className="flex gap-4">
                      {article.image_url && (
                        <div className="w-24 h-16 flex-shrink-0 rounded-sm overflow-hidden bg-zinc-800">
                          <img 
                            src={article.image_url} 
                            alt=""
                            className="w-full h-full object-cover"
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-white line-clamp-2 leading-tight">
                          {article.title}
                        </h3>
                        {article.description && (
                          <p className="text-xs text-zinc-500 mt-1 line-clamp-2">
                            {article.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-[10px] text-zinc-400 font-medium">{article.source}</span>
                          <span className="text-[10px] text-zinc-600">•</span>
                          <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(article.published_at).toLocaleString([], { 
                              month: 'short', 
                              day: 'numeric', 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </span>
                          {article.sentiment && (
                            <>
                              <span className="text-[10px] text-zinc-600">•</span>
                              <span className={`text-[10px] ${getSentimentColor(article.sentiment)}`}>
                                {article.sentiment}
                              </span>
                            </>
                          )}
                          <ExternalLink className="w-3 h-3 text-zinc-600 ml-auto" />
                        </div>
                        {article.tags?.length > 0 && (
                          <div className="flex gap-1 mt-2 flex-wrap">
                            {article.tags.map((tag, j) => (
                              <Badge 
                                key={j} 
                                variant="outline" 
                                className="rounded-none text-[9px] px-1 py-0 h-4 text-orange-500 border-orange-500/30"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {filteredNews.length === 0 && (
                  <div className="p-8 text-center text-zinc-500">
                    No news articles found
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="col-span-4 space-y-4">
          {/* Trending Topics */}
          <Card className="nexus-card">
            <CardHeader className="card-header-terminal">
              <CardTitle className="card-header-title flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                Trending Topics
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="space-y-2">
                {allTags.slice(0, 10).map((tag, i) => {
                  const count = news.filter(n => n.tags?.includes(tag)).length;
                  return (
                    <div 
                      key={tag}
                      className="flex items-center justify-between py-1.5 px-2 hover:bg-zinc-800/30 rounded-sm cursor-pointer"
                      onClick={() => setSelectedTag(tag)}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-zinc-500">{i + 1}</span>
                        <span className="text-sm text-white">{tag}</span>
                      </div>
                      <Badge variant="outline" className="rounded-none text-[10px] text-zinc-500">
                        {count}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Breaking News Alert */}
          <Card className="nexus-card border-orange-500/50">
            <CardHeader className="card-header-terminal bg-orange-500/10">
              <CardTitle className="card-header-title text-orange-500 flex items-center gap-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                Breaking News
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              {news.slice(0, 3).map((article, i) => (
                <div 
                  key={i}
                  className="py-2 border-b border-zinc-800/50 last:border-0 cursor-pointer hover:text-orange-500"
                  onClick={() => window.open(article.url, '_blank')}
                >
                  <p className="text-xs text-white line-clamp-2">{article.title}</p>
                  <span className="text-[10px] text-zinc-500 mt-1">
                    {new Date(article.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default NewsPage;
