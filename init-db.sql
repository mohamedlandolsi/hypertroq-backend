-- Initialize database with required extensions

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create comment for tracking
COMMENT ON EXTENSION vector IS 'Vector similarity search for AI embeddings';
COMMENT ON EXTENSION "uuid-ossp" IS 'UUID generation functions';
