# Legal and ethical use

> Orientation only, not legal advice. Laws differ by country. Ask a lawyer
> where you operate before relying on any of this.

## The line REB draws

Reverse-engineering software you lawfully own is broadly protected.
Reverse-engineering **another organization's internal knowledge** is not. That
knowledge usually reaches you through people, documents or system access, and
those are exactly the channels trade-secret and unfair-competition law treat as
improper. Relevant rules include:

- Turkish Commercial Code art. 54–63
- Turkish Penal Code art. 239 and 133
- EU Directive 2016/943
- US DTSA

REB therefore runs in three modes, enforced by the engine:

| Mode | Use it when | Not for |
|---|---|---|
| `self` | You own or run the organization | — |
| `engaged` | You hold a **written** mandate from it: consulting, or due diligence the seller consents to | Analysing an organization that has not agreed |
| `public` | You only use public records and signals | Internal documents, exports, chats, interviews. The engine rejects them |

## Do not use REB to

- obtain, or ask employees or ex-employees for, a competitor's confidential information;
- create pretexts: fake customer enquiries, fake job applications, fake supplier calls;
- process material you received in breach of an NDA or a duty of loyalty;
- record people without consent;
- scrape sites whose terms forbid it.

In `public` mode, render observations and questions only. Do not render
judgements about a named private company. Labels like "red flag" or "fraud" can
be defamatory.

## Personal data

Employee names, salaries, customer lists, chats and recordings are personal data
under KVKK (Turkey), GDPR (EU), PDPL (Saudi Arabia) and UAE PDPL.

- REB is **local-first**. The ledger lives in `<workspace>/.reb/`, which is git-ignored.
- Names, phones, e-mails, IBANs and national ids are **pseudonymized at ingest** (pseudonymized, **not anonymized**: the originals and the local map still identify people).
  - Names are found in chat senders, as a common given name followed by a surname, after an honorific (Mr, Dr, Sayın, السيد …) or before Bey/Hanım. This is a heuristic: pass `--name` (MCP `names`) for anyone it may miss.
  - Tokens are salted per engagement, so a token in a shared report cannot be matched to a guessed name without the workspace.
  - Only names are kept in the map (`.reb/pseudonyms.json`). E-mails, phones, IBANs and ids are re-derived and never written down. Set `REB_PSEUDONYM_DIR` to keep the map outside the workspace, so a copy or zip of the workspace does not carry it.
- **Interviews and chat exports need a `legal_basis`**, such as a consent or notice reference, before they can be ingested.
- Sending content to a hosted model, or sharing a report abroad, may be a **cross-border transfer**. In Turkey that falls under KVKK art. 9 (standard contracts plus notification, or another basis). Use a local model or mask the data first if you have no basis.
- Set a retention date on the engagement and delete the workspace when it passes.

## Reports are not warranties

REB rejects claims that use warranty language (verified, guaranteed, مضمون,
موثّق, kesinlikle…). A report states what the evidence shows, with grades and
dates. It is not an audit, a valuation, legal advice or a guarantee.

In many countries some of those activities are **regulated professions**. In
Turkey, for example, certifying financial statements is reserved for licensed
accountants (SMMM/YMM). Bring those professionals in. Their signed outputs then
become sources with their own authority.
