delete from housemaid_applicant_reservations;
delete from housemaid_applicant_visa;
delete from housemaid_applicant_expectedarrival;
delete from housemaid_applicant_arrival;
delete from housemaid_applicant_deliver;
delete from housemaid_applicant_returnback;
delete from housemaid_applicant_resell;
delete from housemaid_applicant_selltest;
delete from housemaid_applicant_returnbackfromfirstsponsor;
delete from housemaid_applicant_returnbackfromlastsponsor;
delete from housemaid_applicant_backtocountryafterfirstsponsor;
delete from housemaid_applicant_backtocountryafterlastsponsor;

update housemaid_applicant_applications set state='application';



delete from account_partial_reconcile;
delete from account_move_line;
delete from account_invoice;
delete from account_move;
delete from account_payment;

select count (*) from account_partial_reconcile;
select count (*) from account_move_line;
select count (*) from account_invoice;
select count (*) from account_move;
select count (*) from account_payment;

