import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, CheckCircle, XCircle } from 'lucide-react';
import { documentService } from '../../services/documentService';
import { DocumentUploadResponse } from '../../types';
import './FileUpload.css';

interface FileUploadProps {
    onUploadComplete?: (results: DocumentUploadResponse[]) => void;
}

interface FileWithProgress {
    file: File;
    progress: number;
    status: 'pending' | 'uploading' | 'success' | 'error';
    message?: string;
    result?: DocumentUploadResponse;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
    const [files, setFiles] = useState<FileWithProgress[]>([]);
    const [category, setCategory] = useState('');
    const [isUploading, setIsUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newFiles: FileWithProgress[] = acceptedFiles.map((file) => ({
            file,
            progress: 0,
            status: 'pending',
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/plain': ['.txt'],
            'text/csv': ['.csv'],
        },
        multiple: true,
    });

    const removeFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setIsUploading(true);

        try {
            // Upload files
            const filesToUpload = files.map((f) => f.file);
            const results = await documentService.uploadFiles(
                filesToUpload,
                category || undefined
            );

            // Update file statuses with results
            setFiles((prev) =>
                prev.map((fileItem, index) => ({
                    ...fileItem,
                    status: results[index].status === 'completed' ? 'success' : 'error',
                    message: results[index].message,
                    result: results[index],
                    progress: 100,
                }))
            );

            if (onUploadComplete) {
                onUploadComplete(results);
            }

            // Clear successful uploads after a delay
            setTimeout(() => {
                setFiles((prev) => prev.filter((f) => f.status === 'error'));
            }, 3000);
        } catch (error) {
            console.error('Upload error:', error);
            setFiles((prev) =>
                prev.map((f) => ({
                    ...f,
                    status: 'error',
                    message: 'Upload failed',
                }))
            );
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="file-upload-container">
            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
            >
                <input {...getInputProps()} />
                <Upload size={48} className="upload-icon" />
                <p className="dropzone-text">
                    {isDragActive
                        ? 'Drop files here...'
                        : 'Drag & drop files here, or click to select'}
                </p>
                <p className="dropzone-subtext">Supports PDF, DOCX, TXT, CSV (max 10MB)</p>
            </div>

            {files.length > 0 && (
                <div className="files-section">
                    <div className="category-input">
                        <label htmlFor="category">Category (optional):</label>
                        <input
                            id="category"
                            type="text"
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            placeholder="e.g., Product Documentation, FAQ"
                            disabled={isUploading}
                        />
                    </div>

                    <div className="files-list">
                        {files.map((fileItem, index) => (
                            <div key={index} className="file-item">
                                <div className="file-info">
                                    <FileText size={20} className="file-icon" />
                                    <div className="file-details">
                                        <span className="file-name">{fileItem.file.name}</span>
                                        <span className="file-size">
                                            {(fileItem.file.size / 1024).toFixed(1)} KB
                                        </span>
                                    </div>
                                </div>

                                <div className="file-status">
                                    {fileItem.status === 'success' && (
                                        <CheckCircle size={20} className="status-icon success" />
                                    )}
                                    {fileItem.status === 'error' && (
                                        <XCircle size={20} className="status-icon error" />
                                    )}
                                    {!isUploading && fileItem.status === 'pending' && (
                                        <button
                                            onClick={() => removeFile(index)}
                                            className="remove-btn"
                                            title="Remove file"
                                        >
                                            <X size={18} />
                                        </button>
                                    )}
                                </div>

                                {fileItem.message && (
                                    <p
                                        className={`file-message ${fileItem.status === 'error' ? 'error' : 'success'
                                            }`}
                                    >
                                        {fileItem.message}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={handleUpload}
                        className="btn btn-primary upload-btn"
                        disabled={isUploading}
                    >
                        {isUploading ? (
                            <>
                                <div className="spinner" />
                                Uploading...
                            </>
                        ) : (
                            <>
                                <Upload size={20} />
                                Upload {files.length} File{files.length > 1 ? 's' : ''}
                            </>
                        )}
                    </button>
                </div>
            )}
        </div>
    );
};
