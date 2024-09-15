-- Pre-Scripts

update account_account set currency_id = (select currency_id from res_company);
update account_journal set currency_id = (select currency_id from res_company);







