import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { 
  BookOpen, Calendar, Eye, Tag, ArrowLeft, Share2, 
  Clock, User, ChevronRight, Twitter, Facebook, Linkedin, Copy
} from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { toast } from "sonner";
import { Helmet } from "react-helmet";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function BlogPostPage() {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [relatedPosts, setRelatedPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showShareMenu, setShowShareMenu] = useState(false);

  useEffect(() => {
    if (slug) {
      fetchPost();
    }
  }, [slug]);

  const fetchPost = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/blog/posts/${slug}`);
      setPost(res.data);
      fetchRelatedPosts();
    } catch (error) {
      console.error("Failed to fetch post:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRelatedPosts = async () => {
    try {
      const res = await axios.get(`${API}/blog/related/${slug}`);
      setRelatedPosts(res.data.related);
    } catch (error) {
      console.error("Failed to fetch related posts:", error);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  const estimateReadTime = (content) => {
    const words = content?.split(" ").length || 0;
    return Math.max(1, Math.ceil(words / 200));
  };

  const shareUrl = window.location.href;

  const handleShare = (platform) => {
    const text = post?.title || "";
    let url = "";
    
    switch (platform) {
      case "twitter":
        url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`;
        break;
      case "facebook":
        url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
        break;
      case "linkedin":
        url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
        break;
      case "copy":
        navigator.clipboard.writeText(shareUrl);
        toast.success("Link copied to clipboard!");
        setShowShareMenu(false);
        return;
    }
    
    if (url) {
      window.open(url, "_blank", "width=600,height=400");
    }
    setShowShareMenu(false);
  };

  // Convert content with basic markdown-like formatting
  const renderContent = (content) => {
    if (!content) return null;
    
    // Split by double newlines for paragraphs
    const paragraphs = content.split(/\n\n+/);
    
    return paragraphs.map((para, i) => {
      // Check for headings
      if (para.startsWith("# ")) {
        return <h1 key={i} className="text-3xl font-bold mt-8 mb-4">{para.slice(2)}</h1>;
      }
      if (para.startsWith("## ")) {
        return <h2 key={i} className="text-2xl font-bold mt-8 mb-4">{para.slice(3)}</h2>;
      }
      if (para.startsWith("### ")) {
        return <h3 key={i} className="text-xl font-bold mt-6 mb-3">{para.slice(4)}</h3>;
      }
      
      // Check for bullet lists
      if (para.includes("\n- ") || para.startsWith("- ")) {
        const items = para.split("\n- ").filter(Boolean);
        return (
          <ul key={i} className="list-disc list-inside space-y-2 my-4 text-text-secondary">
            {items.map((item, j) => (
              <li key={j}>{item.replace(/^- /, "")}</li>
            ))}
          </ul>
        );
      }
      
      // Regular paragraph
      return (
        <p key={i} className="text-text-secondary leading-relaxed mb-4">
          {para}
        </p>
      );
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-pink-500/30 border-t-pink-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center px-6">
        <BookOpen className="w-16 h-16 text-text-muted mb-4" />
        <h1 className="text-2xl font-bold mb-2">Post Not Found</h1>
        <p className="text-text-secondary mb-6">The article you're looking for doesn't exist.</p>
        <Link to="/blog">
          <Button>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Blog
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>{`${post.title || 'Blog Post'} | AI Companion Blog`}</title>
        <meta name="description" content={post.meta_description || post.excerpt || ''} />
        <meta name="keywords" content={(post.meta_keywords || []).join(", ")} />
        <meta name="author" content={post.author || 'Admin'} />
        
        {/* Open Graph */}
        <meta property="og:title" content={post.title || ''} />
        <meta property="og:description" content={post.meta_description || post.excerpt || ''} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={shareUrl} />
        {post.featured_image && <meta property="og:image" content={post.featured_image} />}
        <meta property="article:published_time" content={post.published_at || ''} />
        <meta property="article:author" content={post.author || 'Admin'} />
        <meta property="article:section" content={post.category || 'General'} />
        {post.tags?.map((tag, i) => (
          <meta key={i} property="article:tag" content={tag} />
        ))}
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={post.title} />
        <meta name="twitter:description" content={post.meta_description} />
        {post.featured_image && <meta name="twitter:image" content={post.featured_image} />}
        
        <link rel="canonical" href={shareUrl} />
        
        {/* Structured Data for SEO */}
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.meta_description,
            "image": post.featured_image || "",
            "author": {
              "@type": "Person",
              "name": post.author
            },
            "datePublished": post.published_at,
            "dateModified": post.updated_at,
            "publisher": {
              "@type": "Organization",
              "name": "AI Companion"
            },
            "mainEntityOfPage": {
              "@type": "WebPage",
              "@id": shareUrl
            }
          })}
        </script>
      </Helmet>

      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="sticky top-0 z-50 glass-heavy border-b border-white/5">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link to="/blog" className="flex items-center gap-3 text-text-secondary hover:text-white transition-colors">
                <ArrowLeft className="w-5 h-5" />
                <span className="hidden sm:inline">Back to Blog</span>
              </Link>
              
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Button
                    onClick={() => setShowShareMenu(!showShareMenu)}
                    variant="ghost"
                    size="icon"
                    data-testid="share-btn"
                  >
                    <Share2 className="w-5 h-5" />
                  </Button>
                  
                  {showShareMenu && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="absolute right-0 top-full mt-2 glass rounded-xl p-2 min-w-[160px]"
                    >
                      <button
                        onClick={() => handleShare("twitter")}
                        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-white/5 text-sm"
                      >
                        <Twitter className="w-4 h-4 text-blue-400" />
                        Twitter
                      </button>
                      <button
                        onClick={() => handleShare("facebook")}
                        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-white/5 text-sm"
                      >
                        <Facebook className="w-4 h-4 text-blue-600" />
                        Facebook
                      </button>
                      <button
                        onClick={() => handleShare("linkedin")}
                        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-white/5 text-sm"
                      >
                        <Linkedin className="w-4 h-4 text-blue-500" />
                        LinkedIn
                      </button>
                      <button
                        onClick={() => handleShare("copy")}
                        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-white/5 text-sm"
                      >
                        <Copy className="w-4 h-4" />
                        Copy Link
                      </button>
                    </motion.div>
                  )}
                </div>
                
                <Link to="/">
                  <Button variant="ghost" className="text-text-secondary hover:text-white">
                    Home
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* Article */}
        <article className="py-12 px-6">
          <div className="max-w-4xl mx-auto">
            {/* Category Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Link to={`/blog?category=${post.category}`}>
                <span className="inline-block px-3 py-1 rounded-full bg-pink-500/20 text-pink-400 text-sm font-medium mb-6">
                  {post.category}
                </span>
              </Link>
            </motion.div>

            {/* Title */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-3xl sm:text-4xl lg:text-5xl font-heading font-bold mb-6"
            >
              {post.title}
            </motion.h1>

            {/* Meta */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex flex-wrap items-center gap-4 text-text-secondary mb-8"
            >
              <span className="flex items-center gap-2">
                <User className="w-4 h-4" />
                {post.author}
              </span>
              <span className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {formatDate(post.published_at)}
              </span>
              <span className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                {estimateReadTime(post.content)} min read
              </span>
              <span className="flex items-center gap-2">
                <Eye className="w-4 h-4" />
                {post.views} views
              </span>
            </motion.div>

            {/* Featured Image */}
            {post.featured_image && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="aspect-video rounded-2xl overflow-hidden mb-10"
              >
                <img
                  src={post.featured_image}
                  alt={post.title}
                  className="w-full h-full object-cover"
                />
              </motion.div>
            )}

            {/* Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="prose prose-invert prose-pink max-w-none"
            >
              {renderContent(post.content)}
            </motion.div>

            {/* Tags */}
            {post.tags && post.tags.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-10 pt-8 border-t border-white/10"
              >
                <div className="flex items-center gap-3 flex-wrap">
                  <Tag className="w-4 h-4 text-text-muted" />
                  {post.tags.map((tag) => (
                    <Link
                      key={tag}
                      to={`/blog?tag=${tag}`}
                      className="px-3 py-1 rounded-full bg-white/5 text-text-secondary text-sm hover:bg-white/10 transition-colors"
                    >
                      #{tag}
                    </Link>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        </article>

        {/* Related Posts */}
        {relatedPosts.length > 0 && (
          <section className="py-12 px-6 border-t border-white/5">
            <div className="max-w-7xl mx-auto">
              <h2 className="text-2xl font-bold mb-8">Related Articles</h2>
              <div className="grid md:grid-cols-3 gap-6">
                {relatedPosts.map((relatedPost) => (
                  <Link key={relatedPost.id} to={`/blog/${relatedPost.slug}`}>
                    <div className="glass rounded-2xl overflow-hidden hover:border-pink-500/30 border border-transparent transition-all group">
                      <div className="aspect-video bg-gradient-to-br from-pink-500/20 to-purple-500/20 overflow-hidden">
                        {relatedPost.featured_image ? (
                          <img
                            src={relatedPost.featured_image}
                            alt={relatedPost.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <BookOpen className="w-8 h-8 text-pink-500/50" />
                          </div>
                        )}
                      </div>
                      <div className="p-5">
                        <span className="text-xs font-medium text-pink-400 uppercase">
                          {relatedPost.category}
                        </span>
                        <h3 className="font-bold mt-2 line-clamp-2 group-hover:text-pink-400 transition-colors">
                          {relatedPost.title}
                        </h3>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* CTA Section */}
        <section className="py-16 px-6 border-t border-white/5">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-2xl font-bold mb-4">Ready to Experience AI Companionship?</h2>
            <p className="text-text-secondary mb-8">
              Join thousands of users who have found meaningful connections with our AI companions.
            </p>
            <Link to="/auth">
              <Button size="lg" className="bg-gradient-to-r from-pink-500 to-rose-500">
                Get Started Free
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
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
