-- Money Radar — License System Database Schema
-- Run after feeds.fun's own migrations

-- 授权码表
CREATE TABLE IF NOT EXISTS mr_licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_hash VARCHAR(64) NOT NULL UNIQUE,     -- SHA256 of the license code
    user_id UUID NOT NULL DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL DEFAULT 'basic', -- basic, pro, enterprise
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, revoked, expired
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_mr_licenses_code_hash ON mr_licenses(code_hash);
CREATE INDEX idx_mr_licenses_user_id ON mr_licenses(user_id);
CREATE INDEX idx_mr_licenses_expires_at ON mr_licenses(expires_at);

-- 用户 RSS 源订阅表
CREATE TABLE IF NOT EXISTS mr_user_feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    feed_url TEXT NOT NULL,
    feed_title TEXT,
    feed_description TEXT,
    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, feed_url)
);

CREATE INDEX idx_mr_user_feeds_user_id ON mr_user_feeds(user_id);

-- 用户评分规则表
CREATE TABLE IF NOT EXISTS mr_user_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    required_tags TEXT[] NOT NULL DEFAULT '{}',
    excluded_tags TEXT[] NOT NULL DEFAULT '{}',
    score INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mr_user_rules_user_id ON mr_user_rules(user_id);
