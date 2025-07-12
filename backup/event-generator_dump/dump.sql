CREATE SCHEMA IF NOT EXISTS email_sender;

CREATE TABLE email_sender.template (
    id UUID PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    template_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

COMMENT ON TABLE email_sender.template IS 'Таблица шаблонов для email_sender';

COMMENT ON COLUMN email_sender.template.id IS 'Уникальный идентификатор шаблона';
COMMENT ON COLUMN email_sender.template.name IS 'Наименование шаблона';
COMMENT ON COLUMN email_sender.template.description IS 'Описание шаблона';
COMMENT ON COLUMN email_sender.template.template_type IS 'Тип шаблона';
COMMENT ON COLUMN email_sender.template.content IS 'HTML код шаблона';
COMMENT ON COLUMN email_sender.template.created_at IS 'Дата создания шаблона';
COMMENT ON COLUMN email_sender.template.updated_at IS 'Дата последнего
