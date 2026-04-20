MACHINE CookieModel
SETS
    STATUS = {granted, none}
VARIABLES
    user_consent_cookie
INVARIANT
    user_consent_cookie : STATUS
INITIALISATION
    user_consent_cookie := none
OPERATIONS
    VerifyInitialState = 
    SELECT user_consent_cookie = none
    THEN skip 
    END;

    AcceptConsent = BEGIN user_consent_cookie := granted END;
    RejectConsent = BEGIN user_consent_cookie := none END
END