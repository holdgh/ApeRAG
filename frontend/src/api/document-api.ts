import { request } from '@/services';

// Document content and chunks API methods

/**
 * Get document original content
 */
export const getDocumentContent = async (params: {
  collectionId: string;
  documentId: string;
}) => {
  return request.get(`/api/v1/collections/${params.collectionId}/documents/${params.documentId}/content`);
};

/**
 * Get document chunks
 */
export const getDocumentChunks = async (params: {
  collectionId: string;
  documentId: string;
}) => {
  return request.get(`/api/v1/collections/${params.collectionId}/documents/${params.documentId}/chunks`);
}; 