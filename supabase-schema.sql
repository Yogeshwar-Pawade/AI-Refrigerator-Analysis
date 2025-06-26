
-- Chat conversations table
CREATE TABLE chat_conversations (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  summary_id TEXT NOT NULL REFERENCES summaries(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for chat tables
CREATE INDEX idx_chat_conversations_summary_id ON chat_conversations(summary_id);
CREATE INDEX idx_chat_conversations_created_at ON chat_conversations(created_at DESC);
CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at ASC);

-- Create a function to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_summaries_updated_at 
    BEFORE UPDATE ON summaries 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_conversations_updated_at 
    BEFORE UPDATE ON chat_conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for now (adjust for production)
CREATE POLICY "Allow all operations on summaries" ON summaries
FOR ALL USING (true);

CREATE POLICY "Allow all operations on chat_conversations" ON chat_conversations
FOR ALL USING (true);

CREATE POLICY "Allow all operations on chat_messages" ON chat_messages
FOR ALL USING (true);

-- Add analysis column to summaries table
ALTER TABLE summaries ADD COLUMN IF NOT EXISTS analysis JSONB;

-- Create index for analysis column
CREATE INDEX IF NOT EXISTS idx_summaries_analysis ON summaries USING GIN (analysis);

-- Refrigerator diagnoses table for specialized appliance troubleshooting
CREATE TABLE IF NOT EXISTS refrigerator_diagnoses (
    id SERIAL PRIMARY KEY,
    video_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    video_url TEXT NOT NULL,
    user_description TEXT,
    brand TEXT,
    model TEXT,
    issue_category TEXT,
    severity_level TEXT,
    diagnosis_result TEXT NOT NULL,
    solutions TEXT NOT NULL,
    audio_summary TEXT,
    ai_model TEXT DEFAULT 'gemini-2.0-flash-001',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for refrigerator diagnoses
CREATE INDEX IF NOT EXISTS idx_refrigerator_diagnoses_video_id ON refrigerator_diagnoses(video_id);
CREATE INDEX IF NOT EXISTS idx_refrigerator_diagnoses_brand ON refrigerator_diagnoses(brand);
CREATE INDEX IF NOT EXISTS idx_refrigerator_diagnoses_issue_category ON refrigerator_diagnoses(issue_category);
CREATE INDEX IF NOT EXISTS idx_refrigerator_diagnoses_severity_level ON refrigerator_diagnoses(severity_level);
CREATE INDEX IF NOT EXISTS idx_refrigerator_diagnoses_created_at ON refrigerator_diagnoses(created_at DESC);

-- Enable Row Level Security for refrigerator diagnoses
ALTER TABLE refrigerator_diagnoses ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations on refrigerator diagnoses
CREATE POLICY "Allow all operations on refrigerator_diagnoses" ON refrigerator_diagnoses
FOR ALL USING (true);

-- Add the missing refrigerator_type column to refrigerator_diagnoses table
ALTER TABLE refrigerator_diagnoses ADD COLUMN IF NOT EXISTS refrigerator_type TEXT;

-- Update chat_conversations to use diagnosis_id instead of summary_id
-- Add diagnosis_id column if it doesn't exist
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS diagnosis_id TEXT;

-- Drop foreign key constraint if it exists
ALTER TABLE chat_conversations DROP CONSTRAINT IF EXISTS chat_conversations_summary_id_fkey;

-- Drop summary_id column if it exists  
ALTER TABLE chat_conversations DROP COLUMN IF EXISTS summary_id;

-- Create index for diagnosis_id
CREATE INDEX IF NOT EXISTS idx_chat_conversations_diagnosis_id ON chat_conversations(diagnosis_id); 