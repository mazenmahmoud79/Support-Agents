/**
 * TypeScript type definitions for the application.
 */

// ==================== Enums ====================

export enum FileType {
    PDF = 'pdf',
    DOCX = 'docx',
    TXT = 'txt',
    CSV = 'csv',
}

export enum MessageRole {
    USER = 'user',
    ASSISTANT = 'assistant',
    SYSTEM = 'system',
}

export enum DocumentStatus {
    PENDING = 'pending',
    PROCESSING = 'processing',
    COMPLETED = 'completed',
    FAILED = 'failed',
}

// ==================== API Types ====================

export interface Tenant {
    id: number;
    tenant_id: string;
    name: string;
    slug?: string;  // URL-safe identifier for public API
    api_key: string;
    created_at: string;
    is_active: boolean;
}

export interface Document {
    id: number;
    tenant_id: string;
    filename: string;
    file_type: FileType;
    file_size: number;
    category?: string;
    chunk_count: number;
    upload_date: string;
    status: DocumentStatus;
    error_message?: string;
}

export interface DocumentUploadResponse {
    document_id: number;
    filename: string;
    file_type: FileType;
    file_size: number;
    status: DocumentStatus;
    message: string;
}

export interface ChatMessage {
    role: MessageRole;
    content: string;
}

export interface SourceDocument {
    document_id: number;
    filename: string;
    chunk_index: number;
    relevance_score: number;
    snippet: string;
}

export interface ChatResponse {
    response: string;
    session_id: string;
    sources?: SourceDocument[];
    response_time: number;
    timestamp: string;
}

export interface Analytics {
    tenant_id: string;
    date: string;
    query_count: number;
    avg_response_time: number;
    successful_queries: number;
    failed_queries: number;
    documents_uploaded: number;
}

export interface DocumentStats {
    total_documents: number;
    total_chunks: number;
    total_size_bytes: number;
    documents_by_type: Record<string, number>;
    recent_uploads: Document[];
}

// ==================== UI State Types ====================

export interface AuthState {
    isAuthenticated: boolean;
    tenant: Tenant | null;
    apiKey: string | null;
    login: (apiKey: string) => Promise<void>;
    register: (name: string) => Promise<{ apiKey: string }>;
    logout: () => void;
}

export interface UploadProgress {
    filename: string;
    progress: number;
    status: 'uploading' | 'processing' | 'completed' | 'failed';
    error?: string;
}

// ==================== Tenant Context Types ====================

export enum Industry {
    TECHNOLOGY = 'technology',
    HEALTHCARE = 'healthcare',
    ECOMMERCE = 'ecommerce',
    FINANCE = 'finance',
    EDUCATION = 'education',
    REAL_ESTATE = 'real_estate',
    RETAIL = 'retail',
    MANUFACTURING = 'manufacturing',
    HOSPITALITY = 'hospitality',
    LEGAL = 'legal',
    CONSULTING = 'consulting',
    INSURANCE = 'insurance',
    TELECOMMUNICATIONS = 'telecommunications',
    OTHER = 'other',
}

export enum ToneOfVoice {
    PROFESSIONAL = 'professional',
    FRIENDLY = 'friendly',
    FORMAL = 'formal',
    CASUAL = 'casual',
    EMPATHETIC = 'empathetic',
    TECHNICAL = 'technical',
    ENTHUSIASTIC = 'enthusiastic',
}

export enum LanguageStyle {
    SIMPLE = 'simple',
    CONVERSATIONAL = 'conversational',
    TECHNICAL = 'technical',
    BUSINESS = 'business',
}

export enum ResponseLength {
    CONCISE = 'concise',
    BALANCED = 'balanced',
    DETAILED = 'detailed',
}

export interface TenantContext {
    id: number;
    tenant_id: string;

    // Basic Company Info
    company_name?: string;
    company_description?: string;
    industry: Industry;
    target_audience?: string;

    // Response Style Settings
    tone_of_voice: ToneOfVoice;
    language_style: LanguageStyle;
    response_length: ResponseLength;

    // Branding & Messaging
    greeting_style?: string;
    sign_off_style?: string;
    keywords_to_use?: string;
    keywords_to_avoid?: string;
    unique_selling_points?: string;

    // Support Contact (Fallback)
    support_email?: string;
    support_phone?: string;
    support_hours?: string;
    support_url?: string;

    // Custom Instructions
    custom_instructions?: string;

    // Metadata
    created_at: string;
    updated_at: string;
}

export interface TenantContextUpdate {
    company_name?: string;
    company_description?: string;
    industry?: Industry;
    target_audience?: string;
    tone_of_voice?: ToneOfVoice;
    language_style?: LanguageStyle;
    response_length?: ResponseLength;
    greeting_style?: string;
    sign_off_style?: string;
    keywords_to_use?: string;
    keywords_to_avoid?: string;
    unique_selling_points?: string;
    support_email?: string;
    support_phone?: string;
    support_hours?: string;
    support_url?: string;
    custom_instructions?: string;
}

export interface ContextOptions {
    industries: Array<{ value: string; label: string }>;
    tones: Array<{ value: string; label: string }>;
    language_styles: Array<{ value: string; label: string }>;
    response_lengths: Array<{ value: string; label: string }>;
}

