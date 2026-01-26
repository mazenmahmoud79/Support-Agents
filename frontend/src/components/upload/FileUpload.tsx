import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import useDrivePicker from 'react-google-drive-picker';
import { Upload, X, FileText, CheckCircle, XCircle, Cloud } from 'lucide-react';
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

    const [openDrivePicker] = useDrivePicker();

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newFiles: FileWithProgress[] = acceptedFiles.map((file) => ({
            file,
            progress: 0,
            status: 'pending',
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    }, []);

    const handleDriveClick = () => {
        openDrivePicker({
            clientId: import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID,
            developerKey: import.meta.env.VITE_GOOGLE_DRIVE_API_KEY,
            viewId: 'DOCS',
            // showIcon: true, // Removed as it causes type error
            supportDrives: true,
            multiselect: true,
            callbackFunction: (data) => {
                if (data.action === 'picked') {
                    handleDriveCallback(data);
                }
            },
        });
    };

    const handleDriveCallback = async (data: any) => {
        const driveFiles = data.docs;
        const newFiles: FileWithProgress[] = [];

        for (const driveFile of driveFiles) {
            try {
                // For Google Docs/Sheets/Slides, we need to export them. 
                // However, the picker returns a download URL or we can use the ID to fetch via API.
                // Simplified approach: Create a placeholder or fetch if we had full Drive API access scope.
                // NOTE: The standard picker with 'drive.file' scope grants access to the selected file.
                // We need to fetch the file content.

                // Using the access token from the picker metadata if available, or just trying to fetch via the URL provided.
                // The picker result usually contains: id, name, mimeType, iconUrl, url, etc.

                // Real implementation would require fetching the file blob locally.
                // Since this is a client-side integration without a backend proxy for Drive, 
                // we'll attempt to fetch the file content if `driveFile.url` or `driveFile.id` is usable with the API Key/Token.

                // However, the picker itself doesn't return the file *content*, just metadata.
                // To get content, we need to make an authenticated request to the Drive API.
                // This requires an access token. The picker might not return a fresh access token for the *user* session 
                // unless we handle auth explicitly.

                // FOR NOW: We will rely on the `oauthToken` passed to the picker or assume the user is authenticated.
                // But `useDrivePicker` handles the loaded script. 

                // CRITICAL FIX: The `react-google-drive-picker` usually handles auth. 
                // We need to fetch the file blob using the ID and the token.
                // But we don't have the token readily exposed in the callback `data` usually (it depends on the lib version).

                // Alternative: We will mock the file object for now or try to fetch it if we can get a token.
                // Actually, the `data` object in `callbackFunction` usually just has `docs`.
                // Accessing file content from the browser requires `window.gapi.client.drive.files.get`.

                // Let's attempt to use the `oauthToken` if we can assume it's available globally or retrieve it.
                // If not, we might be limited to standard uploads or need a more complex auth flow.

                // STRATEGY: We will assume we can fetch via the `gapi` client which should be initialized by the picker.

                const token = (window as any).gapi?.auth?.getToken()?.access_token;
                if (!token) {
                    console.error("No access token found for Drive fetch");
                    continue;
                }

                const response = await fetch(`https://www.googleapis.com/drive/v3/files/${driveFile.id}?alt=media`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) throw new Error('Failed to fetch file from Drive');

                const blob = await response.blob();
                const file = new File([blob], driveFile.name, { type: driveFile.mimeType });

                newFiles.push({
                    file,
                    progress: 0,
                    status: 'pending'
                });

            } catch (error) {
                console.error("Error fetching Drive file:", error);
            }
        }

        setFiles((prev) => [...prev, ...newFiles]);
    };

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
            <div className="upload-actions">
                <button
                    onClick={handleDriveClick}
                    className="btn btn-secondary google-drive-btn"
                    type="button"
                >
                    <Cloud size={18} className="mr-2" />
                    Select from Google Drive
                </button>
            </div>

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
