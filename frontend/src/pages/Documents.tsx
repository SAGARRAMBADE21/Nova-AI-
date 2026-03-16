import { useState, useEffect, useRef } from 'react';
import { FileText, ShieldCheck, UploadCloud, X } from 'lucide-react';
import { uploadDocument, listDocuments, type Document } from '@/lib/api';

const SUPPORTED = ['.pdf', '.docx', '.xlsx', '.csv', '.txt', '.json', '.xml', '.md'];

const Documents = () => {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState('');
  const [dbType, setDbType] = useState<'public' | 'private'>('public');
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const [uploadOk, setUploadOk] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    try {
      setLoadingDocs(true);
      const data = await listDocuments();
      setDocuments(data.documents);
    } catch {
      // silently ignore — no docs yet
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const pickFile = (f: File) => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED.includes(ext)) {
      setUploadMsg(`✕ Unsupported file type. Allowed: ${SUPPORTED.join(', ')}`);
      setUploadOk(false);
      return;
    }
    setFile(f);
    setUploadMsg('');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  };

  const handleSubmit = async () => {
    if (!file) { setUploadMsg('✕ Please select a file first.'); setUploadOk(false); return; }
    setUploading(true);
    setUploadMsg('');
    try {
      await uploadDocument(file, category || 'general', dbType);
      setUploadMsg('✓ Document uploaded and ingested successfully.');
      setUploadOk(true);
      setFile(null);
      setCategory('');
      setDbType('public');
      fetchDocs();
    } catch (err) {
      setUploadMsg(`✕ ${err instanceof Error ? err.message : 'Upload failed.'}`);
      setUploadOk(false);
    } finally {
      setUploading(false);
    }
  };

  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-brand-charcoal">Knowledge Base</h1>
        <p className="text-brand-grayBody mt-2">Upload and manage the documents that power your AI.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Upload Form */}
        <div className="lg:col-span-5 space-y-4">
          {/* Drop zone */}
          <div
            className={`border-2 border-dashed rounded-3xl p-10 text-center transition-colors cursor-pointer group ${dragging ? 'border-brand-orange bg-orange-50' : 'border-brand-border hover:border-brand-orange'}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={SUPPORTED.join(',')}
              className="hidden"
              onChange={e => { if (e.target.files?.[0]) pickFile(e.target.files[0]); }}
            />
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="text-brand-orange w-6 h-6 shrink-0" />
                <span className="text-sm font-semibold text-brand-charcoal truncate max-w-[200px]">{file.name}</span>
                <button
                  onClick={e => { e.stopPropagation(); setFile(null); setUploadMsg(''); }}
                  className="text-brand-grayBody hover:text-red-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <div className="bg-brand-lightBg w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <UploadCloud className="text-brand-orange w-8 h-8" />
                </div>
                <h4 className="text-brand-charcoal font-bold">Upload Document</h4>
                <p className="text-sm text-brand-grayBody mt-2 leading-relaxed">
                  Drag &amp; drop files here, or click to browse.<br />
                  <span className="text-xs font-semibold">PDF, DOCX, XLSX, CSV, TXT, JSON, XML, MD</span>
                </p>
              </>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Category</label>
            <input
              className="w-full px-4 py-2.5 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none"
              placeholder="e.g. HR, Finance, IT"
              type="text"
              value={category}
              onChange={e => setCategory(e.target.value)}
            />
          </div>

          {/* Access Control */}
          <div className="p-4 bg-brand-lightBg rounded-2xl border border-brand-border">
            <label className="block text-xs font-bold text-brand-charcoal mb-4 uppercase tracking-tight">Access Control</label>
            <div className="space-y-3">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  className="mt-1 text-brand-charcoal focus:ring-brand-charcoal"
                  name="db_type"
                  type="radio"
                  checked={dbType === 'public'}
                  onChange={() => setDbType('public')}
                />
                <div>
                  <span className="block text-sm font-bold text-brand-charcoal">Public Database</span>
                  <span className="block text-xs text-brand-grayBody">Visible to all employees</span>
                </div>
              </label>
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  className="mt-1 text-brand-charcoal focus:ring-brand-charcoal"
                  name="db_type"
                  type="radio"
                  checked={dbType === 'private'}
                  onChange={() => setDbType('private')}
                />
                <div>
                  <span className="block text-sm font-bold text-brand-charcoal">Confidential Database</span>
                  <span className="block text-xs text-brand-grayBody">Managers &amp; Admins only</span>
                </div>
              </label>
            </div>
          </div>

          {uploadMsg && (
            <p className={`text-sm font-semibold ${uploadOk ? 'text-green-600' : 'text-red-500'}`}>{uploadMsg}</p>
          )}

          <button
            className="w-full bg-brand-charcoal text-white py-3.5 rounded-full font-bold hover:shadow-lg transition-all active:scale-95 disabled:opacity-50"
            onClick={handleSubmit}
            disabled={uploading || !file}
          >
            {uploading ? 'Uploading & Ingesting…' : 'Upload & Ingest Document'}
          </button>
        </div>

        {/* Document List */}
        <div className="lg:col-span-7">
          <div className="border border-brand-border rounded-2xl overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-brand-lightBg text-[10px] uppercase tracking-widest font-bold text-brand-grayBody border-b border-brand-border">
                <tr>
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4">Category</th>
                  <th className="px-6 py-4">Access</th>
                  <th className="px-6 py-4">Ingested</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border text-sm">
                {loadingDocs ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-brand-grayBody">Loading documents…</td>
                  </tr>
                ) : documents.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-brand-grayBody">No documents ingested yet. Upload one to get started.</td>
                  </tr>
                ) : documents.map((doc, i) => (
                  <tr key={i} className="hover:bg-brand-lightBg/30">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {doc.db_type === 'private'
                          ? <ShieldCheck className="w-4 h-4 text-brand-grayBody shrink-0" />
                          : <FileText className="w-4 h-4 text-brand-grayBody shrink-0" />
                        }
                        <span className="font-medium text-brand-charcoal truncate max-w-[200px]">{doc.source}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-brand-grayBody text-xs capitalize">{doc.category}</td>
                    <td className="px-6 py-4">
                      {doc.db_type === 'private'
                        ? <span className="text-xs font-bold text-brand-orange bg-orange-50 px-2 py-0.5 rounded">Confidential</span>
                        : <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded">Public</span>
                      }
                    </td>
                    <td className="px-6 py-4 text-brand-grayBody text-xs">
                      {doc.ingested_at ? new Date(doc.ingested_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Documents;

