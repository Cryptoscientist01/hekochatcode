import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link, useSearchParams } from "react-router-dom";
import { 
  BookOpen, Calendar, Eye, Tag, ChevronLeft, ChevronRight, 
  Search, ArrowRight, Clock, User
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { Helmet } from "react-helmet-async";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function BlogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [posts, setPosts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");

  const currentPage = parseInt(searchParams.get("page") || "1");
  const currentCategory = searchParams.get("category") || "";
  const currentTag = searchParams.get("tag") || "";

  useEffect(() => {
    fetchPosts();
    fetchCategories();
    fetchTags();
  }, [currentPage, currentCategory, currentTag]);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      let url = `${API}/blog/posts?page=${currentPage}&limit=9`;
      if (currentCategory) url += `&category=${currentCategory}`;
      if (currentTag) url += `&tag=${currentTag}`;
      
      const res = await axios.get(url);
      setPosts(res.data.posts);
      setTotalPages(res.data.pages);
    } catch (error) {
      console.error("Failed to fetch posts:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/blog/categories`);
      setCategories(res.data.categories);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  };

  const fetchTags = async () => {
    try {
      const res = await axios.get(`${API}/blog/tags`);
      setTags(res.data.tags);
    } catch (error) {
      console.error("Failed to fetch tags:", error);
    }
  };

  const handlePageChange = (page) => {
    const params = new URLSearchParams(searchParams);
    params.set("page", page.toString());
    setSearchParams(params);
  };

  const handleCategoryFilter = (category) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    params.set("page", "1");
    setSearchParams(params);
  };

  const handleTagFilter = (tag) => {
    const params = new URLSearchParams();
    if (tag) params.set("tag", tag);
    params.set("page", "1");
    setSearchParams(params);
  };

  const filteredPosts = posts.filter(post =>
    post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.excerpt.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  const estimateReadTime = (excerpt) => {
    const words = excerpt?.split(" ").length || 0;
    return Math.max(1, Math.ceil(words / 200));
  };

  return (
    <>
      <Helmet>
        <title>Blog | AI Companion Insights & Tips</title>
        <meta name="description" content="Explore our blog for the latest insights on AI companions, virtual relationships, and digital connection tips." />
        <meta name="keywords" content="AI companion, virtual girlfriend, AI chat, digital relationship, AI blog" />
        <meta property="og:title" content="Blog | AI Companion Insights" />
        <meta property="og:description" content="Discover tips, guides, and insights about AI companions and virtual relationships." />
        <meta property="og:type" content="website" />
        <link rel="canonical" href={`${window.location.origin}/blog`} />
      </Helmet>

      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="sticky top-0 z-50 glass-heavy border-b border-white/5">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link to="/" className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-heading font-bold">Blog</span>
              </Link>
              
              <div className="flex items-center gap-4">
                <Link to="/">
                  <Button variant="ghost" className="text-text-secondary hover:text-white">
                    Home
                  </Button>
                </Link>
                <Link to="/auth">
                  <Button className="bg-gradient-to-r from-pink-500 to-rose-500">
                    Get Started
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="relative py-16 px-6 overflow-hidden">
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
          </div>
          
          <div className="max-w-4xl mx-auto text-center relative z-10">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold mb-6"
            >
              Insights & <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-rose-500">Stories</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-lg text-text-secondary max-w-2xl mx-auto mb-8"
            >
              Discover tips, guides, and fascinating insights about AI companions and the future of digital connections.
            </motion.p>
            
            {/* Search */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="relative max-w-md mx-auto"
            >
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              <Input
                data-testid="blog-search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search articles..."
                className="pl-12 h-12 bg-white/5 border-white/10 rounded-full"
              />
            </motion.div>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-12 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-12">
              {/* Posts Grid */}
              <div className="flex-1">
                {/* Active Filters */}
                {(currentCategory || currentTag) && (
                  <div className="mb-8 flex items-center gap-3">
                    <span className="text-text-secondary">Filtering by:</span>
                    {currentCategory && (
                      <span className="px-3 py-1 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center gap-2">
                        {currentCategory}
                        <button onClick={() => handleCategoryFilter("")} className="hover:text-white">×</button>
                      </span>
                    )}
                    {currentTag && (
                      <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center gap-2">
                        #{currentTag}
                        <button onClick={() => handleTagFilter("")} className="hover:text-white">×</button>
                      </span>
                    )}
                  </div>
                )}

                {loading ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="w-8 h-8 border-2 border-pink-500/30 border-t-pink-500 rounded-full animate-spin" />
                  </div>
                ) : filteredPosts.length === 0 ? (
                  <div className="text-center py-16">
                    <BookOpen className="w-16 h-16 text-text-muted mx-auto mb-4" />
                    <h3 className="text-xl font-bold mb-2">No posts found</h3>
                    <p className="text-text-secondary">Check back soon for new content!</p>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredPosts.map((post, i) => (
                      <motion.article
                        key={post.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className="group"
                      >
                        <Link to={`/blog/${post.slug}`} data-testid={`post-${post.slug}`}>
                          <div className="glass rounded-2xl overflow-hidden hover:border-pink-500/30 border border-transparent transition-all">
                            {/* Featured Image */}
                            <div className="aspect-video bg-gradient-to-br from-pink-500/20 to-purple-500/20 overflow-hidden">
                              {post.featured_image ? (
                                <img
                                  src={post.featured_image}
                                  alt={post.title}
                                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <BookOpen className="w-12 h-12 text-pink-500/50" />
                                </div>
                              )}
                            </div>
                            
                            {/* Content */}
                            <div className="p-5">
                              {/* Category */}
                              <span className="text-xs font-medium text-pink-400 uppercase tracking-wide">
                                {post.category}
                              </span>
                              
                              {/* Title */}
                              <h2 className="text-lg font-bold mt-2 mb-3 line-clamp-2 group-hover:text-pink-400 transition-colors">
                                {post.title}
                              </h2>
                              
                              {/* Excerpt */}
                              <p className="text-text-secondary text-sm line-clamp-2 mb-4">
                                {post.excerpt}
                              </p>
                              
                              {/* Meta */}
                              <div className="flex items-center justify-between text-xs text-text-muted">
                                <div className="flex items-center gap-3">
                                  <span className="flex items-center gap-1">
                                    <Calendar className="w-3 h-3" />
                                    {formatDate(post.published_at)}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {estimateReadTime(post.excerpt)} min
                                  </span>
                                </div>
                                <span className="flex items-center gap-1">
                                  <Eye className="w-3 h-3" />
                                  {post.views}
                                </span>
                              </div>
                            </div>
                          </div>
                        </Link>
                      </motion.article>
                    ))}
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-12">
                    <Button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      variant="ghost"
                      size="icon"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </Button>
                    
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let page;
                      if (totalPages <= 5) {
                        page = i + 1;
                      } else if (currentPage <= 3) {
                        page = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        page = totalPages - 4 + i;
                      } else {
                        page = currentPage - 2 + i;
                      }
                      
                      return (
                        <Button
                          key={page}
                          onClick={() => handlePageChange(page)}
                          variant={currentPage === page ? "default" : "ghost"}
                          className={currentPage === page ? "bg-pink-500" : ""}
                        >
                          {page}
                        </Button>
                      );
                    })}
                    
                    <Button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      variant="ghost"
                      size="icon"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </Button>
                  </div>
                )}
              </div>

              {/* Sidebar */}
              <aside className="w-full lg:w-72 space-y-8">
                {/* Categories */}
                <div className="glass rounded-2xl p-6">
                  <h3 className="font-bold mb-4 flex items-center gap-2">
                    <Tag className="w-4 h-4 text-pink-500" />
                    Categories
                  </h3>
                  <div className="space-y-2">
                    {categories.map((cat) => (
                      <button
                        key={cat.name}
                        onClick={() => handleCategoryFilter(cat.name)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between ${
                          currentCategory === cat.name
                            ? "bg-pink-500/20 text-pink-400"
                            : "hover:bg-white/5 text-text-secondary"
                        }`}
                      >
                        <span>{cat.name}</span>
                        <span className="text-xs opacity-60">{cat.count}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tags */}
                {tags.length > 0 && (
                  <div className="glass rounded-2xl p-6">
                    <h3 className="font-bold mb-4">Popular Tags</h3>
                    <div className="flex flex-wrap gap-2">
                      {tags.slice(0, 15).map((tag) => (
                        <button
                          key={tag.name}
                          onClick={() => handleTagFilter(tag.name)}
                          className={`px-3 py-1 rounded-full text-xs transition-colors ${
                            currentTag === tag.name
                              ? "bg-purple-500 text-white"
                              : "bg-white/5 text-text-secondary hover:bg-white/10"
                          }`}
                        >
                          #{tag.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* CTA */}
                <div className="glass rounded-2xl p-6 bg-gradient-to-br from-pink-500/10 to-purple-500/10 border border-pink-500/20">
                  <h3 className="font-bold mb-2">Ready to Connect?</h3>
                  <p className="text-text-secondary text-sm mb-4">
                    Join thousands of users experiencing AI companionship.
                  </p>
                  <Link to="/auth">
                    <Button className="w-full bg-gradient-to-r from-pink-500 to-rose-500">
                      Get Started Free
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </aside>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/5 py-8 px-6">
          <div className="max-w-7xl mx-auto text-center text-text-muted text-sm">
            <p>© {new Date().getFullYear()} AI Companion. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </>
  );
}
