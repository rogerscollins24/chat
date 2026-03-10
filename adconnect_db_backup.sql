--
-- PostgreSQL database dump
--

\restrict RIPgzgnHn8OUhed9PVJa5asnX9Ciz13lcYvX6xIzp0UVfYC9VAtQ8BL2Fxi2gjj

-- Dumped from database version 18.1 (Homebrew)
-- Dumped by pg_dump version 18.1 (Postgres.app)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: senderrole; Type: TYPE; Schema: public; Owner: adconnect_user
--

CREATE TYPE public.senderrole AS ENUM (
    'USER',
    'AGENT'
);


ALTER TYPE public.senderrole OWNER TO adconnect_user;

--
-- Name: sessionstatus; Type: TYPE; Schema: public; Owner: adconnect_user
--

CREATE TYPE public.sessionstatus AS ENUM (
    'OPEN',
    'RESOLVED'
);


ALTER TYPE public.sessionstatus OWNER TO adconnect_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agents; Type: TABLE; Schema: public; Owner: adconnect_user
--

CREATE TABLE public.agents (
    id integer NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    name character varying NOT NULL,
    referral_code character varying NOT NULL,
    is_default_pool boolean,
    created_at timestamp without time zone,
    role character varying(20) DEFAULT 'AGENT'::character varying NOT NULL
);


ALTER TABLE public.agents OWNER TO adconnect_user;

--
-- Name: agents_id_seq; Type: SEQUENCE; Schema: public; Owner: adconnect_user
--

CREATE SEQUENCE public.agents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agents_id_seq OWNER TO adconnect_user;

--
-- Name: agents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adconnect_user
--

ALTER SEQUENCE public.agents_id_seq OWNED BY public.agents.id;


--
-- Name: lead_metadata; Type: TABLE; Schema: public; Owner: adconnect_user
--

CREATE TABLE public.lead_metadata (
    id integer NOT NULL,
    session_id integer,
    ip character varying,
    location character varying,
    browser character varying,
    ad_id character varying,
    agent_referral_code character varying
);


ALTER TABLE public.lead_metadata OWNER TO adconnect_user;

--
-- Name: lead_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: adconnect_user
--

CREATE SEQUENCE public.lead_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lead_metadata_id_seq OWNER TO adconnect_user;

--
-- Name: lead_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adconnect_user
--

ALTER SEQUENCE public.lead_metadata_id_seq OWNED BY public.lead_metadata.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: adconnect_user
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    session_id integer,
    sender_id character varying,
    sender_role public.senderrole,
    text text,
    is_internal boolean,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.messages OWNER TO adconnect_user;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: adconnect_user
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_id_seq OWNER TO adconnect_user;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adconnect_user
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: adconnect_user
--

CREATE TABLE public.sessions (
    id integer NOT NULL,
    user_id character varying,
    user_name character varying,
    user_avatar character varying,
    ad_source character varying,
    assigned_agent_id integer,
    status public.sessionstatus,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.sessions OWNER TO adconnect_user;

--
-- Name: sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: adconnect_user
--

CREATE SEQUENCE public.sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sessions_id_seq OWNER TO adconnect_user;

--
-- Name: sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adconnect_user
--

ALTER SEQUENCE public.sessions_id_seq OWNED BY public.sessions.id;


--
-- Name: agents id; Type: DEFAULT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.agents ALTER COLUMN id SET DEFAULT nextval('public.agents_id_seq'::regclass);


--
-- Name: lead_metadata id; Type: DEFAULT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.lead_metadata ALTER COLUMN id SET DEFAULT nextval('public.lead_metadata_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: sessions id; Type: DEFAULT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.sessions ALTER COLUMN id SET DEFAULT nextval('public.sessions_id_seq'::regclass);


--
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: adconnect_user
--

COPY public.agents (id, email, password_hash, name, referral_code, is_default_pool, created_at, role) FROM stdin;
2	pool@leadpulse.com	$2b$12$R6LoQ8ayyXSbvZ9ULS1BEereHt.JFK2PekuCjBorN9zi8fEu.AwWS	Pool Agent	1XSX1E1V	t	2026-01-31 12:46:02.231954	AGENT
4	herlord@leadpulse.com	$2b$12$1IFj8i1Ek1ey2IbGCcIrt.hCIdBnAy7b8tls3y5XRYSCe4I0mvdM.	Herlord Admin	AX8B2YKN	f	2026-02-01 12:31:57.209158	SUPER_ADMIN
\.


--
-- Data for Name: lead_metadata; Type: TABLE DATA; Schema: public; Owner: adconnect_user
--

COPY public.lead_metadata (id, session_id, ip, location, browser, ad_id, agent_referral_code) FROM stdin;
1	1	\N	\N	Chrome	\N	CSJ91JSE
2	2	\N	\N	\N	\N	DEFAULT_POOL
3	3	\N	\N	\N	\N	CSJ91JSE
4	4	\N	\N	\N	\N	DEFAULT_POOL
5	5	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
6	6	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
7	7	Client IP	User Location	Client Web Application	REF_LINK	1XSX1E1V
8	8	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
9	9	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
10	10	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
11	11	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
12	12	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
13	13	\N	\N	\N	WS-E2E	CSJ91JSE
14	14	\N	\N	\N	WS-E2E	CSJ91JSE
15	15	Client IP	User Location	Client Web Application	REF_LINK	CSJ91JSE
16	16	1.1.1.1	\N	QA	QA123	DEFAULT_POOL
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: adconnect_user
--

COPY public.messages (id, session_id, sender_id, sender_role, text, is_internal, "timestamp") FROM stdin;
1	1	test-user-1	USER	Hello, I need help with my order	f	2026-01-31 12:46:02.243567
2	1	john	AGENT	Hi! I'm happy to help. What can I assist you with?	f	2026-01-31 12:46:02.243595
3	2	test_sender	USER	Hello, this is a test message from PostgreSQL!	f	2026-01-31 15:50:00.700215
4	3	client	USER	Hello!	f	2026-01-31 16:29:36.414071
5	3	client	USER	Hello!	f	2026-01-31 16:48:19.71603
6	5	user-id	USER	hello	f	2026-01-31 17:58:07.513619
7	5	user-id	USER	im stuck	f	2026-01-31 17:58:13.257095
8	5	user-id	USER	fkfjksdn	f	2026-01-31 17:59:36.849739
9	5	agent-1	AGENT	How can I help you today?	f	2026-01-31 18:02:24.782144
10	5	agent-1	AGENT	fklfvnkjvf	f	2026-01-31 18:02:39.687744
11	5	user-id	USER	vklcdcsnkd	f	2026-01-31 18:03:08.849326
12	5	user-id	USER	vijjvjhviosvhudvklevnvnruivpudsn;jk	f	2026-01-31 18:03:26.732718
13	5	user-id	USER	hello sir	f	2026-01-31 18:18:11.457819
14	5	user-id	USER	hello madam	f	2026-01-31 18:18:20.319442
15	5	user-id	USER	how are you doing	f	2026-01-31 18:18:47.824147
16	5	user-id	USER	test 1	f	2026-01-31 18:21:11.801526
17	5	user-id	USER	hey friend	f	2026-01-31 18:21:29.446377
18	5	1	AGENT	How can I help you today?	f	2026-01-31 18:21:42.928931
19	5	1	AGENT	hey	f	2026-01-31 18:21:47.528371
20	6	client-1769873055280-muxdrm1hm	USER	darline	f	2026-01-31 18:49:57.424332
21	7	client-1769873055464-z4m2840au	USER	mitanda	f	2026-01-31 18:50:03.723612
22	7	client-1769873055464-z4m2840au	USER	mitanda	f	2026-01-31 18:50:30.777593
23	6	1	AGENT	How can I help you today?	f	2026-01-31 18:50:50.714585
24	7	client-1769873055464-z4m2840au	USER	mitanda	f	2026-01-31 18:51:02.266208
25	7	client-1769873055464-z4m2840au	USER	vhdg	f	2026-01-31 18:51:32.115788
26	8	client-1769874779726-oixuyxi7m	USER	mitanda	f	2026-01-31 18:53:05.132355
27	10	client-1769933452344-2kaitcfdn	USER	john	f	2026-02-01 11:12:54.900642
28	11	client-1769933457423-xaq3w5fcn	USER	kaaya	f	2026-02-01 11:13:02.897317
29	11	1	AGENT	How can I help you today?	f	2026-02-01 11:16:35.723204
30	10	1	AGENT	Thanks for reaching out!	f	2026-02-01 11:16:47.802354
31	11	1	AGENT	how is your day	f	2026-02-01 11:18:43.411415
32	12	client-1769933957935-7743egrcb	USER	matthwe	f	2026-02-01 11:19:27.376916
33	13	ws-test-a96075a6	USER	hello from ws test	f	2026-02-01 11:31:41.875827
34	14	ws-test-c0ea2dbc	USER	hello from ws test	f	2026-02-01 11:31:52.660407
35	15	client-1769935885369-fgrlwn8pr	USER	hey	f	2026-02-01 11:52:04.282178
36	15	1	AGENT	Thanks for reaching out!	f	2026-02-01 11:52:19.220957
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: adconnect_user
--

COPY public.sessions (id, user_id, user_name, user_avatar, ad_source, assigned_agent_id, status, created_at, updated_at) FROM stdin;
2	test_user_1769863800	Test User	https://via.placeholder.com/150	google	2	OPEN	2026-01-31 15:50:00.69112	2026-01-31 15:50:00.691125
4	test_pool_client	Client B	\N	test	2	OPEN	2026-01-31 16:29:36.409952	2026-01-31 16:29:36.409954
7	client-1769873055464-z4m2840au	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	2	OPEN	2026-01-31 18:24:15.468106	2026-01-31 18:24:15.468116
16	user-1769937641	QA Client	https://example.com/avatar.png	qa_test	2	OPEN	2026-02-01 12:20:41.332448	2026-02-01 12:20:41.332452
1	test-user-1	Test Client	\N	test_migration	\N	OPEN	2026-01-31 12:46:02.238537	2026-02-01 12:36:43.454996
3	test_john_client	Client A	\N	test	\N	OPEN	2026-01-31 16:29:36.400246	2026-02-01 12:36:43.455007
5	user-id	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	RESOLVED	2026-01-31 17:58:01.172885	2026-02-01 12:36:43.455008
6	client-1769873055280-muxdrm1hm	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	OPEN	2026-01-31 18:24:15.285353	2026-02-01 12:36:43.455009
8	client-1769874779726-oixuyxi7m	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	OPEN	2026-01-31 18:52:59.740301	2026-02-01 12:36:43.45501
9	client-1769933542473-ahrn4kuc8	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	OPEN	2026-02-01 11:12:22.490887	2026-02-01 12:36:43.45501
10	client-1769933452344-2kaitcfdn	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	OPEN	2026-02-01 11:12:48.85168	2026-02-01 12:36:43.455011
11	client-1769933457423-xaq3w5fcn	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	OPEN	2026-02-01 11:12:58.472816	2026-02-01 12:36:43.455012
12	client-1769933957935-7743egrcb	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	\N	OPEN	2026-02-01 11:19:17.956228	2026-02-01 12:36:43.455013
13	ws-test-a96075a6	WS Test User	https://picsum.photos/seed/ws-test/200	WS Test	\N	OPEN	2026-02-01 11:31:41.867472	2026-02-01 12:36:43.455014
14	ws-test-c0ea2dbc	WS Test User	https://picsum.photos/seed/ws-test/200	WS Test	\N	OPEN	2026-02-01 11:31:52.655772	2026-02-01 12:36:43.455014
15	client-1769935885369-fgrlwn8pr	Lead Candidate	https://picsum.photos/seed/lead/200	Facebook Ads - Summer Campaign	2	OPEN	2026-02-01 11:51:36.020997	2026-02-01 12:38:25.416788
\.


--
-- Name: agents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adconnect_user
--

SELECT pg_catalog.setval('public.agents_id_seq', 4, true);


--
-- Name: lead_metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adconnect_user
--

SELECT pg_catalog.setval('public.lead_metadata_id_seq', 16, true);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adconnect_user
--

SELECT pg_catalog.setval('public.messages_id_seq', 36, true);


--
-- Name: sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adconnect_user
--

SELECT pg_catalog.setval('public.sessions_id_seq', 16, true);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: lead_metadata lead_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.lead_metadata
    ADD CONSTRAINT lead_metadata_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: ix_agents_email; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE UNIQUE INDEX ix_agents_email ON public.agents USING btree (email);


--
-- Name: ix_agents_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_agents_id ON public.agents USING btree (id);


--
-- Name: ix_agents_is_default_pool; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_agents_is_default_pool ON public.agents USING btree (is_default_pool);


--
-- Name: ix_agents_referral_code; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE UNIQUE INDEX ix_agents_referral_code ON public.agents USING btree (referral_code);


--
-- Name: ix_lead_metadata_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_lead_metadata_id ON public.lead_metadata USING btree (id);


--
-- Name: ix_lead_metadata_session_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE UNIQUE INDEX ix_lead_metadata_session_id ON public.lead_metadata USING btree (session_id);


--
-- Name: ix_messages_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_messages_id ON public.messages USING btree (id);


--
-- Name: ix_messages_session_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_messages_session_id ON public.messages USING btree (session_id);


--
-- Name: ix_sessions_assigned_agent_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_sessions_assigned_agent_id ON public.sessions USING btree (assigned_agent_id);


--
-- Name: ix_sessions_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE INDEX ix_sessions_id ON public.sessions USING btree (id);


--
-- Name: ix_sessions_user_id; Type: INDEX; Schema: public; Owner: adconnect_user
--

CREATE UNIQUE INDEX ix_sessions_user_id ON public.sessions USING btree (user_id);


--
-- Name: lead_metadata lead_metadata_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.lead_metadata
    ADD CONSTRAINT lead_metadata_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id);


--
-- Name: messages messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id);


--
-- Name: sessions sessions_assigned_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adconnect_user
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_assigned_agent_id_fkey FOREIGN KEY (assigned_agent_id) REFERENCES public.agents(id);


--
-- PostgreSQL database dump complete
--

\unrestrict RIPgzgnHn8OUhed9PVJa5asnX9Ciz13lcYvX6xIzp0UVfYC9VAtQ8BL2Fxi2gjj

