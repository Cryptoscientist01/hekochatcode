import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate, useParams } from "react-router-dom";
import { 
  ArrowLeft, Save, Eye, Trash2, Plus, Image as ImageIcon,
  FileText, Tag, Calendar, Globe, Search, Edit, X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminBlogEditor({ adminToken }) {
  const navigate = useNavigate();
  const { postId } = useParams();
  const isEditing = Boolean(postId);
  
  const [view, setView] = useState(isEditing ? "editor" : "list");
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Form state
  const [formData, setFormData] = useState({
    title: "",
    slug: "",
    content: "",
    excerpt: "",
    meta_description: "",
    meta_keywords: [],
    featured_image: "",
    author: "Admin",
    category: "General",
    tags: [],
    status: "draft"
  });
  
  const [newKeyword, setNewKeyword] = useState("");
  const [newTag, setNewTag] = useState("");

  const authHeaders = {
    headers: { Authorization: `Bearer ${adminToken}` }
  };

  useEffect(() => {
    if (view === "list") {
      fetchPosts();
    }
    if (postId) {
      fetchPost(postId);
    }
  }, [view, postId]);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/blog/posts`, authHeaders);
      setPosts(res.data.posts);
    } catch (error) {
      toast.error("Failed to fetch posts");
    } finally {
      setLoading(false);
    }
  };

  const fetchPost = async (id) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/blog/posts/${id}`, authHeaders);
      setFormData({
        title: res.data.title || "",
        slug: res.data.slug || "",
        content: res.data.content || "",
        excerpt: res.data.excerpt || "",
        meta_description: res.data.meta_description || "",
        meta_keywords: res.data.meta_keywords || [],
        featured_image: res.data.featured_image || "",
        author: res.data.author || "Admin",
        category: res.data.category || "General",
        tags: res.data.tags || [],
        status: res.data.status || "draft"
      });
      setView("editor");
    } catch (error) {
      toast.error("Failed to fetch post");
      navigate("/optimus/blog");
    } finally {
      setLoading(false);
    }
  };

  const generateSlug = (title) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  };

  const handleTitleChange = (e) => {
    const title = e.target.value;
    setFormData(prev => ({
      ...prev,
      title,
      slug: prev.slug || generateSlug(title)
    }));
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addKeyword = () => {
    if (newKeyword.trim() && !formData.meta_keywords.includes(newKeyword.trim())) {
      setFormData(prev => ({
        ...prev,
        meta_keywords: [...prev.meta_keywords, newKeyword.trim()]
      }));
      setNewKeyword("");
    }
  };

  const removeKeyword = (keyword) => {
    setFormData(prev => ({
      ...prev,
      meta_keywords: prev.meta_keywords.filter(k => k !== keyword)
    }));
  };

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag("");
    }
  };

  const removeTag = (tag) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }));
  };

  const handleSave = async (publishNow = false) => {
    if (!formData.title || !formData.content) {
      toast.error("Title and content are required");
      return;
    }

    setSaving(true);
    try {
      const data = {
        ...formData,
        status: publishNow ? "published" : formData.status,
        excerpt: formData.excerpt || formData.content.slice(0, 200) + "...",
        meta_description: formData.meta_description || formData.excerpt || formData.content.slice(0, 160)
      };

      if (isEditing) {
        await axios.put(`${API}/admin/blog/posts/${postId}`, data, authHeaders);
        toast.success(publishNow ? "Post published!" : "Post updated!");
      } else {
        const res = await axios.post(`${API}/admin/blog/posts`, data, authHeaders);
        toast.success(publishNow ? "Post published!" : "Post saved as draft!");
        navigate(`/optimus/blog/${res.data.post.id}`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save post");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this blog post?")) return;
    
    try {
      await axios.delete(`${API}/admin/blog/posts/${id}`, authHeaders);
      toast.success("Post deleted");
      if (isEditing) {
        navigate("/optimus/blog");
      } else {
        fetchPosts();
      }
    } catch (error) {
      toast.error("Failed to delete post");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      slug: "",
      content: "",
      excerpt: "",
      meta_description: "",
      meta_keywords: [],
      featured_image: "",
      author: "Admin",
      category: "General",
      tags: [],
      status: "draft"
    });
    navigate("/optimus/blog");
  };

  const filteredPosts = posts.filter(post =>
    post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categories = ["General", "Tips & Tricks", "Guides", "News", "Updates", "Stories", "Tutorials"];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/optimus/dashboard" className="text-text-secondary hover:text-white transition-colors">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <FileText className="w-5 h-5 text-pink-500" />
                Blog Manager
              </h1>
            </div>
            
            {view === "list" ? (
              <Button
                onClick={() => { resetForm(); setView("editor"); }}
                className="bg-gradient-to-r from-pink-500 to-rose-500"
                data-testid="new-post-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Post
              </Button>
            ) : (
              <div className="flex items-center gap-3">
                <Button
                  onClick={() => { setView("list"); navigate("/optimus/blog"); }}
                  variant="ghost"
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => handleSave(false)}
                  variant="outline"
                  disabled={saving}
                  data-testid="save-draft-btn"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save Draft
                </Button>
                <Button
                  onClick={() => handleSave(true)}
                  className="bg-gradient-to-r from-pink-500 to-rose-500"
                  disabled={saving}
                  data-testid="publish-btn"
                >
                  <Globe className="w-4 h-4 mr-2" />
                  {saving ? "Saving..." : "Publish"}
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {view === "list" ? (
          /* Posts List View */
          <div className="space-y-6">
            {/* Search */}
            <div className="relative max-w-md">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search posts..."
                className="pl-12 bg-white/5 border-white/10"
                data-testid="blog-search-admin"
              />
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-2 border-pink-500/30 border-t-pink-500 rounded-full animate-spin" />
              </div>
            ) : filteredPosts.length === 0 ? (
              <div className="text-center py-16 glass rounded-2xl">
                <FileText className="w-16 h-16 text-text-muted mx-auto mb-4" />
                <h3 className="text-xl font-bold mb-2">No blog posts yet</h3>
                <p className="text-text-secondary mb-6">Create your first post to get started</p>
                <Button onClick={() => setView("editor")} className="bg-gradient-to-r from-pink-500 to-rose-500">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Post
                </Button>
              </div>
            ) : (
              <div className="glass rounded-2xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-white/5">
                    <tr>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Title</th>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary hidden md:table-cell">Category</th>
                      <th className="text-center p-4 text-sm font-medium text-text-secondary hidden sm:table-cell">Status</th>
                      <th className="text-center p-4 text-sm font-medium text-text-secondary hidden sm:table-cell">Views</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPosts.map((post) => (
                      <tr key={post.id} className="border-t border-white/5 hover:bg-white/5">
                        <td className="p-4">
                          <div>
                            <p className="font-medium line-clamp-1">{post.title}</p>
                            <p className="text-sm text-text-secondary">/blog/{post.slug}</p>
                          </div>
                        </td>
                        <td className="p-4 text-text-secondary hidden md:table-cell">{post.category}</td>
                        <td className="p-4 text-center hidden sm:table-cell">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            post.status === "published" 
                              ? "bg-green-500/20 text-green-400" 
                              : "bg-yellow-500/20 text-yellow-400"
                          }`}>
                            {post.status}
                          </span>
                        </td>
                        <td className="p-4 text-center hidden sm:table-cell">{post.views || 0}</td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {post.status === "published" && (
                              <Link to={`/blog/${post.slug}`} target="_blank">
                                <Button variant="ghost" size="icon" title="View">
                                  <Eye className="w-4 h-4" />
                                </Button>
                              </Link>
                            )}
                            <Button
                              onClick={() => navigate(`/optimus/blog/${post.id}`)}
                              variant="ghost"
                              size="icon"
                              title="Edit"
                              data-testid={`edit-post-${post.id}`}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleDelete(post.id)}
                              variant="ghost"
                              size="icon"
                              className="text-red-400 hover:text-red-300"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          /* Editor View */
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Editor */}
            <div className="lg:col-span-2 space-y-6">
              {/* Title */}
              <div className="glass rounded-2xl p-6">
                <label className="block text-sm font-medium mb-2">Post Title *</label>
                <Input
                  value={formData.title}
                  onChange={handleTitleChange}
                  placeholder="Enter an engaging title..."
                  className="text-xl bg-white/5 border-white/10 h-14"
                  data-testid="post-title-input"
                />
              </div>

              {/* Slug */}
              <div className="glass rounded-2xl p-6">
                <label className="block text-sm font-medium mb-2">URL Slug</label>
                <div className="flex items-center gap-2">
                  <span className="text-text-muted">/blog/</span>
                  <Input
                    value={formData.slug}
                    onChange={(e) => handleChange("slug", generateSlug(e.target.value))}
                    placeholder="url-slug"
                    className="flex-1 bg-white/5 border-white/10"
                    data-testid="post-slug-input"
                  />
                </div>
              </div>

              {/* Content */}
              <div className="glass rounded-2xl p-6">
                <label className="block text-sm font-medium mb-2">Content *</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => handleChange("content", e.target.value)}
                  placeholder="Write your blog post content here...

Use markdown-like formatting:
# Heading 1
## Heading 2
### Heading 3

- Bullet point 1
- Bullet point 2

Regular paragraphs with double line breaks between them."
                  rows={20}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-pink-500 focus:outline-none resize-none"
                  data-testid="post-content-input"
                />
              </div>

              {/* Excerpt */}
              <div className="glass rounded-2xl p-6">
                <label className="block text-sm font-medium mb-2">Excerpt (for previews)</label>
                <textarea
                  value={formData.excerpt}
                  onChange={(e) => handleChange("excerpt", e.target.value)}
                  placeholder="Brief summary of the post (auto-generated if left empty)"
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-pink-500 focus:outline-none resize-none"
                />
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* SEO Settings */}
              <div className="glass rounded-2xl p-6">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-pink-500" />
                  SEO Settings
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Meta Description</label>
                    <textarea
                      value={formData.meta_description}
                      onChange={(e) => handleChange("meta_description", e.target.value)}
                      placeholder="SEO description (160 chars max)"
                      rows={3}
                      maxLength={160}
                      className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-pink-500 focus:outline-none text-sm resize-none"
                    />
                    <p className="text-xs text-text-muted mt-1">{formData.meta_description.length}/160</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Meta Keywords</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        value={newKeyword}
                        onChange={(e) => setNewKeyword(e.target.value)}
                        onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
                        placeholder="Add keyword"
                        className="flex-1 bg-white/5 border-white/10 text-sm h-9"
                      />
                      <Button onClick={addKeyword} size="sm" variant="outline">
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {formData.meta_keywords.map((kw) => (
                        <span key={kw} className="px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs flex items-center gap-1">
                          {kw}
                          <button onClick={() => removeKeyword(kw)} className="hover:text-white">
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Post Settings */}
              <div className="glass rounded-2xl p-6">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-pink-500" />
                  Post Settings
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Category</label>
                    <select
                      value={formData.category}
                      onChange={(e) => handleChange("category", e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-pink-500 focus:outline-none text-sm"
                    >
                      {categories.map((cat) => (
                        <option key={cat} value={cat} className="bg-gray-900">{cat}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Author</label>
                    <Input
                      value={formData.author}
                      onChange={(e) => handleChange("author", e.target.value)}
                      className="bg-white/5 border-white/10 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Featured Image URL</label>
                    <Input
                      value={formData.featured_image}
                      onChange={(e) => handleChange("featured_image", e.target.value)}
                      placeholder="https://..."
                      className="bg-white/5 border-white/10 text-sm"
                    />
                    {formData.featured_image && (
                      <div className="mt-2 aspect-video rounded-lg overflow-hidden bg-white/5">
                        <img 
                          src={formData.featured_image} 
                          alt="Preview" 
                          className="w-full h-full object-cover"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="glass rounded-2xl p-6">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-pink-500" />
                  Tags
                </h3>
                
                <div className="flex gap-2 mb-3">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addTag())}
                    placeholder="Add tag"
                    className="flex-1 bg-white/5 border-white/10 text-sm h-9"
                  />
                  <Button onClick={addTag} size="sm" variant="outline">
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag) => (
                    <span key={tag} className="px-2 py-1 rounded-full bg-pink-500/20 text-pink-400 text-xs flex items-center gap-1">
                      #{tag}
                      <button onClick={() => removeTag(tag)} className="hover:text-white">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Delete Button (for existing posts) */}
              {isEditing && (
                <Button
                  onClick={() => handleDelete(postId)}
                  variant="outline"
                  className="w-full text-red-400 border-red-400/30 hover:bg-red-500/10"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Post
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
