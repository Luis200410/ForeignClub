-- PostgreSQL schema for FOREIGN core data domain.
-- Execute with: \i database/foreign_schema.sql (from project root) inside psql connected to the Foreign database.

BEGIN;

CREATE TABLE IF NOT EXISTS core_profile (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) DEFERRABLE INITIALLY IMMEDIATE,
    display_name VARCHAR(120) NOT NULL,
    headline VARCHAR(180) NULL,
    country VARCHAR(100) NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    native_language VARCHAR(80) NULL,
    target_focus VARCHAR(40) NOT NULL DEFAULT 'conversation',
    desired_fluency_level VARCHAR(2) NOT NULL DEFAULT 'B1',
    bio TEXT NULL,
    linkedin_url VARCHAR(200) NULL,
    phone_number VARCHAR(32) NULL,
    onboarding_completed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT core_profile_desired_fluency_level_check CHECK (desired_fluency_level IN ('A1','A2','B1','B2','C1','C2')),
    CONSTRAINT core_profile_target_focus_check CHECK (target_focus IN ('conversation','career','academic','travel','certification'))
);

COMMENT ON TABLE core_profile IS 'Extended learner profile data for FOREIGN members.';

CREATE TABLE IF NOT EXISTS core_learninggoal (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES core_profile(id) ON DELETE CASCADE,
    title VARCHAR(140) NOT NULL,
    focus_area VARCHAR(40) NOT NULL,
    success_metric VARCHAR(180) NOT NULL,
    target_date DATE NULL,
    priority SMALLINT NOT NULL DEFAULT 2,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT core_learninggoal_focus_area_check CHECK (focus_area IN ('conversation','pronunciation','vocabulary','grammar','writing','leadership')),
    CONSTRAINT core_learninggoal_priority_check CHECK (priority IN (1,2,3))
);

COMMENT ON TABLE core_learninggoal IS 'Strategic learning outcomes defined per learner.';

CREATE UNIQUE INDEX IF NOT EXISTS core_learninggoal_primary_idx
    ON core_learninggoal (profile_id)
    WHERE is_primary;

CREATE TABLE IF NOT EXISTS core_availabilitywindow (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES core_profile(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT core_availabilitywindow_day_of_week_check CHECK (day_of_week BETWEEN 1 AND 7),
    CONSTRAINT core_availabilitywindow_time_order_check CHECK (end_time > start_time)
);

COMMENT ON TABLE core_availabilitywindow IS 'Recurring availability slots to schedule live interactions.';

CREATE UNIQUE INDEX IF NOT EXISTS core_availabilitywindow_unique_slot
    ON core_availabilitywindow (profile_id, day_of_week, start_time, end_time);

CREATE TABLE IF NOT EXISTS core_interactionpreference (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL UNIQUE REFERENCES core_profile(id) ON DELETE CASCADE,
    preferred_session_format VARCHAR(20) NOT NULL DEFAULT 'live',
    preferred_group_size SMALLINT NOT NULL DEFAULT 4,
    availability_notes TEXT NULL,
    communication_channel VARCHAR(20) NOT NULL DEFAULT 'email',
    notification_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    consent_to_research BOOLEAN NOT NULL DEFAULT FALSE,
    prefers_native_coach BOOLEAN NOT NULL DEFAULT TRUE,
    prefers_peer_feedback BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT core_interactionpreference_session_format_check CHECK (preferred_session_format IN ('live','coaching','gameplay','async')),
    CONSTRAINT core_interactionpreference_channel_check CHECK (communication_channel IN ('email','whatsapp','telegram','sms')),
    CONSTRAINT core_interactionpreference_group_size_check CHECK (preferred_group_size BETWEEN 1 AND 12)
);

COMMENT ON TABLE core_interactionpreference IS 'Engagement preferences captured during onboarding & coaching.';

CREATE TABLE IF NOT EXISTS core_skillassessment (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES core_profile(id) ON DELETE CASCADE,
    assessment_type VARCHAR(32) NOT NULL,
    fluency_level VARCHAR(2) NOT NULL DEFAULT 'B1',
    score NUMERIC(5,2) NULL,
    assessed_by VARCHAR(140) NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NULL,
    evidence_url VARCHAR(200) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT core_skillassessment_type_check CHECK (assessment_type IN ('placement','coach_review','self','gameplay')),
    CONSTRAINT core_skillassessment_level_check CHECK (fluency_level IN ('A1','A2','B1','B2','C1','C2'))
);

COMMENT ON TABLE core_skillassessment IS 'Snapshot of learner performance across multiple assessment types.';

CREATE INDEX IF NOT EXISTS skill_assess_profile_idx
    ON core_skillassessment (profile_id, assessed_at DESC);

CREATE TABLE IF NOT EXISTS core_progresslog (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES core_profile(id) ON DELETE CASCADE,
    summary VARCHAR(200) NOT NULL,
    details TEXT NULL,
    impact_rating SMALLINT NOT NULL DEFAULT 3,
    logged_by VARCHAR(120) NOT NULL,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT core_progresslog_rating_check CHECK (impact_rating BETWEEN 1 AND 5)
);

COMMENT ON TABLE core_progresslog IS 'Qualitative progress notes used by mentors and program leads.';

COMMIT;
