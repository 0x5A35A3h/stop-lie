--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.19
-- Dumped by pg_dump version 9.5.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 1 (class 3079 OID 12361)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 2206 (class 0 OID 0)
-- Dependencies: 1
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- TOC entry 3 (class 3079 OID 218137)
-- Name: dict_xsyn; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS dict_xsyn WITH SCHEMA public;


--
-- TOC entry 2207 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION dict_xsyn; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION dict_xsyn IS 'text search dictionary template for extended synonym processing';


--
-- TOC entry 2 (class 3079 OID 218142)
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- TOC entry 2208 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


SET search_path = public, pg_catalog;

--
-- TOC entry 226 (class 1255 OID 218193)
-- Name: docs_tsvector_trigger(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION docs_tsvector_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.tsv :=
    setweight(to_tsvector(coalesce(new.doc_author,'')), 'A') ||
    setweight(to_tsvector(coalesce(new.doc_title,'')), 'A') ||
    setweight(to_tsvector(coalesce(new.doc_text,'')), 'A') ||
    setweight(to_tsvector(coalesce(new.doc_link,'')), 'A');
  return new;
end
$$;


ALTER FUNCTION public.docs_tsvector_trigger() OWNER TO postgres;

--
-- TOC entry 1680 (class 3600 OID 218194)
-- Name: russian_ispell; Type: TEXT SEARCH DICTIONARY; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH DICTIONARY russian_ispell (
    TEMPLATE = pg_catalog.ispell,
    dictfile = 'russian', afffile = 'russian', stopwords = 'russian' );


ALTER TEXT SEARCH DICTIONARY russian_ispell OWNER TO postgres;

--
-- TOC entry 1681 (class 3600 OID 218195)
-- Name: russian_xsyn1; Type: TEXT SEARCH DICTIONARY; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH DICTIONARY russian_xsyn1 (
    TEMPLATE = xsyn_template,
    rules = 'russian_synonyms1', matchorig = 'true', matchsynonyms = 'true', keeporig = 'true', keepsynonyms = 'true' );


ALTER TEXT SEARCH DICTIONARY russian_xsyn1 OWNER TO postgres;

--
-- TOC entry 1682 (class 3600 OID 218196)
-- Name: russian_xsyn2; Type: TEXT SEARCH DICTIONARY; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH DICTIONARY russian_xsyn2 (
    TEMPLATE = xsyn_template,
    rules = 'russian_synonyms2', matchorig = 'true', matchsynonyms = 'true', keeporig = 'true', keepsynonyms = 'true' );


ALTER TEXT SEARCH DICTIONARY russian_xsyn2 OWNER TO postgres;

--
-- TOC entry 1699 (class 3602 OID 218197)
-- Name: ru_search; Type: TEXT SEARCH CONFIGURATION; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH CONFIGURATION ru_search (
    PARSER = pg_catalog."default" );

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR asciiword WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR word WITH russian_ispell, russian_stem;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR numword WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR email WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR url WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR host WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR sfloat WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR version WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR hword_numpart WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR hword_part WITH russian_ispell, russian_stem;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR hword_asciipart WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR numhword WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR asciihword WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR hword WITH russian_ispell, russian_stem;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR url_path WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR file WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR "float" WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR "int" WITH simple;

ALTER TEXT SEARCH CONFIGURATION ru_search
    ADD MAPPING FOR uint WITH simple;


ALTER TEXT SEARCH CONFIGURATION ru_search OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 183 (class 1259 OID 218198)
-- Name: docs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE docs (
    id integer NOT NULL,
    doc_title text,
    doc_date_str character varying(100),
    doc_link character varying(2000),
    doc_text text,
    source_id integer,
    downloaded_date timestamp without time zone,
    tsv tsvector,
    doc_date timestamp without time zone,
    doc_author text,
    doc_author_link text,
    doc_type_id integer,
    doc_fbid character varying(50),
    doc_comment_fbid character varying(50),
    doc_reply_comment_fbid character varying(50),
    doc_author_fbid character varying(50),
    doc_reply_to_author_fbid character varying(50),
    doc_reply_to_author text
);


ALTER TABLE docs OWNER TO postgres;

--
-- TOC entry 184 (class 1259 OID 218204)
-- Name: docs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE docs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE docs_id_seq OWNER TO postgres;

--
-- TOC entry 2209 (class 0 OID 0)
-- Dependencies: 184
-- Name: docs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE docs_id_seq OWNED BY docs.id;


--
-- TOC entry 185 (class 1259 OID 218214)
-- Name: sources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE sources (
    id integer NOT NULL,
    src_type character varying(50),
    url character varying(2000),
    text_selector character varying(2000),
    title_selector character varying(2000),
    date_selector character varying(2000),
    link_selector character varying(2000),
    check_interval integer,
    telegram_send character varying(2000),
    title_regexp character varying(2000),
    date_regexp character varying(2000),
    link_regexp character varying(2000),
    host character varying(255),
    keyword text,
    doc_type_id integer,
    max_posts integer,
    name character varying
);


ALTER TABLE sources OWNER TO postgres;

--
-- TOC entry 186 (class 1259 OID 218220)
-- Name: sources_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sources_id_seq OWNER TO postgres;

--
-- TOC entry 2210 (class 0 OID 0)
-- Dependencies: 186
-- Name: sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sources_id_seq OWNED BY sources.id;


--
-- TOC entry 187 (class 1259 OID 218222)
-- Name: sources_telegram; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE sources_telegram (
    id integer NOT NULL,
    source_id integer,
    telegram_user_id integer
);


ALTER TABLE sources_telegram OWNER TO postgres;

--
-- TOC entry 188 (class 1259 OID 218225)
-- Name: sources_telegram_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sources_telegram_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sources_telegram_id_seq OWNER TO postgres;

--
-- TOC entry 2211 (class 0 OID 0)
-- Dependencies: 188
-- Name: sources_telegram_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sources_telegram_id_seq OWNED BY sources_telegram.id;


--
-- TOC entry 189 (class 1259 OID 218227)
-- Name: sp_doc_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE sp_doc_type (
    id integer NOT NULL,
    doc_type text
);


ALTER TABLE sp_doc_type OWNER TO postgres;

--
-- TOC entry 190 (class 1259 OID 218233)
-- Name: sp_doc_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sp_doc_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sp_doc_type_id_seq OWNER TO postgres;

--
-- TOC entry 2212 (class 0 OID 0)
-- Dependencies: 190
-- Name: sp_doc_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sp_doc_type_id_seq OWNED BY sp_doc_type.id;


--
-- TOC entry 191 (class 1259 OID 218235)
-- Name: sp_telegram_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE sp_telegram_users (
    id integer NOT NULL,
    first_name character varying(255),
    last_name character varying(255),
    telegram_user_id integer
);


ALTER TABLE sp_telegram_users OWNER TO postgres;

--
-- TOC entry 192 (class 1259 OID 218241)
-- Name: sp_telegram_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sp_telegram_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sp_telegram_users_id_seq OWNER TO postgres;

--
-- TOC entry 2213 (class 0 OID 0)
-- Dependencies: 192
-- Name: sp_telegram_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sp_telegram_users_id_seq OWNED BY sp_telegram_users.id;


--
-- TOC entry 2052 (class 2604 OID 218243)
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY docs ALTER COLUMN id SET DEFAULT nextval('docs_id_seq'::regclass);


--
-- TOC entry 2053 (class 2604 OID 218245)
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sources ALTER COLUMN id SET DEFAULT nextval('sources_id_seq'::regclass);


--
-- TOC entry 2054 (class 2604 OID 218246)
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sources_telegram ALTER COLUMN id SET DEFAULT nextval('sources_telegram_id_seq'::regclass);


--
-- TOC entry 2055 (class 2604 OID 218247)
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sp_doc_type ALTER COLUMN id SET DEFAULT nextval('sp_doc_type_id_seq'::regclass);


--
-- TOC entry 2056 (class 2604 OID 218248)
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sp_telegram_users ALTER COLUMN id SET DEFAULT nextval('sp_telegram_users_id_seq'::regclass);


--
-- TOC entry 2189 (class 0 OID 218198)
-- Dependencies: 183
-- Data for Name: docs; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 2214 (class 0 OID 0)
-- Dependencies: 184
-- Name: docs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('docs_id_seq', 1, false);


--
-- TOC entry 2191 (class 0 OID 218214)
-- Dependencies: 185
-- Data for Name: sources; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (1, 'rss', 'http://flb.ru/rss/', '.main-content .row .article-descr, article', '', '', '', 60, NULL, '', '', '', NULL, '', 10, 0, 'Агентство федеральных расследований FLB.ru');
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (4, 'rss', 'https://munscanner.com/feed/', 'article.post div.post-inner', '', '', '', 60, '49838937', '', '', '', 'http://munscanner.blogspot.com', '', 2, 0, 'Муниципальный сканер');
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (5, 'rss', 'https://news.rambler.ru/rss/moscow_city/', '.article__head, .article__paragraph', '', '', '', 30, NULL, '', '', '', NULL, '', 11, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (6, 'rss', 'https://life.ru/xml/feed.xml?hashtag=%D0%BC%D0%BE%D1%81%D0%BA%D0%B2%D0%B0', '.post-page-subtitle, .content-note', '', '', '', 30, NULL, '', '', '', NULL, '', 11, 20, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (8, 'rss', 'https://rss.newsru.com/top/main/', '.mainhead, .explaindate, .maintext p', '', '', '', 30, NULL, '', '', '', NULL, '', 2, NULL, 'Newsru.com');
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (9, 'rss', 'http://static.feed.rbc.ru/rbc/logical/footer/news.rss', '.rbcslider__slide[data-index="0"] .article__header__title, .rbcslider__slide[data-index="0"] .article__text p', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (10, 'rss', 'https://life.ru/xml/feed.xml?hashtag=%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8', '.post-page-subtitle, .content-note', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 20, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (11, 'css', 'http://www.metronews.ru/novosti/', '.article-body', '.material_item h4', '', '.material_item a', 30, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (12, 'css', 'http://www.the-village.ru/news', '.article-text', '.post-item .post-title', '', '.post-item a', 30, NULL, '', '', '', NULL, '', 2, 30, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (13, 'rss', 'https://tvrain.ru/export/rss/all.xml', '.document-lead, .document-content__text p', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 30, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (14, 'rss', 'http://polit.ru/feeds/news/', '.content .text', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (15, 'rss', 'https://republic.ru/export/all.xml', '.post-content', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 20, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (16, 'rss', 'https://www.gazeta.ru/export/rss/lenta.xml', '.article-text-body', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (17, 'rss', 'https://lenta.ru/rss', '.b-topic__content', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 20, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (18, 'css', 'http://radiovesti.ru/news', '.insides-page__news__text', '.news__item-title', '', '.news__item-title', 30, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (19, 'rss', 'http://izvestia.ru/xml/rss/all.xml', 'article.article-content', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 20, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (20, 'rss', 'http://www.vedomosti.ru/rss/news', '.b-news_wrapper-first article.b-news-item:first-of-type .b-news-item__text', '', '', '', 30, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (21, 'css', 'http://m.echo.msk.ru/mainnews/', '.txt', '.evtitle a', '.evdate', '.evtitle a', 30, NULL, '', '', '', NULL, '', 11, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (22, 'rss', 'http://www.newsmsk.com/rss/', '.news_head_inner, .news_date, .article_text', '', '', '', 30, NULL, '', '', '', NULL, '', 11, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (23, 'rss', 'https://noodleremover.news/feed', '.section-inner', '', '', '', 60, NULL, '', '', '', NULL, '', 10, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (24, 'rss', 'http://www.m24.ru/rss.xml', NULL, '', '', '', 30, NULL, '', '', '', NULL, '', 11, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (25, 'rss', 'https://regnum.ru/rss/russian/fd-central/moscow', NULL, '', '', '', 30, NULL, '', '', '', NULL, '', 11, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (26, 'css', 'https://snob.ru/news/', 'article .lead, article .meta, article .text', '.col-entry .box .title', '.col-entry .box .time', '.col-entry > a', 20, NULL, '', '', '', NULL, '', 2, 0, NULL);
INSERT INTO sources (id, src_type, url, text_selector, title_selector, date_selector, link_selector, check_interval, telegram_send, title_regexp, date_regexp, link_regexp, host, keyword, doc_type_id, max_posts, name) VALUES (27, 'css', 'https://utro.ru/news/', '.news__lead, .io-article-bod', '.news-listing > li > a .news-listing__title', '.news-listing > li > a time', '.news-listing > li > a', 20, NULL, '', '', '', NULL, '', 2, 20, NULL);


--
-- TOC entry 2215 (class 0 OID 0)
-- Dependencies: 186
-- Name: sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('sources_id_seq', 30, true);


--
-- TOC entry 2193 (class 0 OID 218222)
-- Dependencies: 187
-- Data for Name: sources_telegram; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 2216 (class 0 OID 0)
-- Dependencies: 188
-- Name: sources_telegram_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('sources_telegram_id_seq', 1, true);


--
-- TOC entry 2195 (class 0 OID 218227)
-- Dependencies: 189
-- Data for Name: sp_doc_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO sp_doc_type (id, doc_type) VALUES (1, 'Региональные новости');
INSERT INTO sp_doc_type (id, doc_type) VALUES (2, 'Федеральные новости');
INSERT INTO sp_doc_type (id, doc_type) VALUES (3, 'Нормативный правовой акт');
INSERT INTO sp_doc_type (id, doc_type) VALUES (10, 'Тематическая статья');
INSERT INTO sp_doc_type (id, doc_type) VALUES (5, 'Сообщение на форуме');
INSERT INTO sp_doc_type (id, doc_type) VALUES (4, 'Тема на форуме');
INSERT INTO sp_doc_type (id, doc_type) VALUES (11, 'Московские новости');


--
-- TOC entry 2217 (class 0 OID 0)
-- Dependencies: 190
-- Name: sp_doc_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('sp_doc_type_id_seq', 11, true);


--
-- TOC entry 2197 (class 0 OID 218235)
-- Dependencies: 191
-- Data for Name: sp_telegram_users; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 2218 (class 0 OID 0)
-- Dependencies: 192
-- Name: sp_telegram_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('sp_telegram_users_id_seq', 1, true);


--
-- TOC entry 2064 (class 2606 OID 218250)
-- Name: docs_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY docs
    ADD CONSTRAINT docs_pk PRIMARY KEY (id);


--
-- TOC entry 2067 (class 2606 OID 218254)
-- Name: sources_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sources
    ADD CONSTRAINT sources_pk PRIMARY KEY (id);


--
-- TOC entry 2069 (class 2606 OID 218256)
-- Name: sources_telegram_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sources_telegram
    ADD CONSTRAINT sources_telegram_pkey PRIMARY KEY (id);


--
-- TOC entry 2071 (class 2606 OID 218258)
-- Name: sp_doc_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sp_doc_type
    ADD CONSTRAINT sp_doc_type_pkey PRIMARY KEY (id);


--
-- TOC entry 2073 (class 2606 OID 218260)
-- Name: sp_telegram_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sp_telegram_users
    ADD CONSTRAINT sp_telegram_users_pkey PRIMARY KEY (id);


--
-- TOC entry 2057 (class 1259 OID 218261)
-- Name: doc_author_fbid_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX doc_author_fbid_idx ON public.docs USING btree (doc_author_fbid);


--
-- TOC entry 2058 (class 1259 OID 218262)
-- Name: doc_author_link_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX doc_author_link_idx ON public.docs USING btree (doc_author_link);


--
-- TOC entry 2059 (class 1259 OID 218263)
-- Name: doc_comment_fbid_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX doc_comment_fbid_idx ON public.docs USING btree (doc_comment_fbid);


--
-- TOC entry 2060 (class 1259 OID 218264)
-- Name: doc_fbid_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX doc_fbid_idx ON public.docs USING btree (doc_fbid);


--
-- TOC entry 2061 (class 1259 OID 218265)
-- Name: doc_type_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX doc_type_idx ON public.docs USING btree (doc_type_id);


--
-- TOC entry 2062 (class 1259 OID 218266)
-- Name: docs_author_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX docs_author_idx ON public.docs USING btree (doc_author);


--
-- TOC entry 2065 (class 1259 OID 218267)
-- Name: docs_tsv_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX docs_tsv_idx ON public.docs USING gin (tsv);


--
-- TOC entry 2074 (class 2620 OID 218272)
-- Name: docs_tsvector_update; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER docs_tsvector_update BEFORE INSERT OR UPDATE ON public.docs FOR EACH ROW EXECUTE PROCEDURE docs_tsvector_trigger();


--
-- TOC entry 2205 (class 0 OID 0)
-- Dependencies: 9
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

