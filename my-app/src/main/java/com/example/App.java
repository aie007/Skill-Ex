package com.example;
import com.microsoft.playwright.*;
import de.prob.scripting.Api;
import de.prob.statespace.*;
import com.google.inject.Guice;
import com.google.inject.Injector;
import de.prob.MainModule;
import de.prob.animator.domainobjects.EvalResult;
import de.prob.animator.domainobjects.AbstractEvalResult;


public class App {
    public static void main(String[] args) throws Exception {
        Injector injector = Guice.createInjector(new MainModule());
        Api api = injector.getInstance(Api.class);
        StateSpace stateSpace = api.b_load("CookieModel.mch");
        Trace trace = new Trace(stateSpace);
        if (!trace.getCurrentState().getOutTransitions().isEmpty()) {
            trace = trace.add(trace.getCurrentState().getOutTransitions().get(0));
        }

        try (Playwright playwright = Playwright.create()) {
            Browser browser = playwright.firefox().launch();
            BrowserContext context = browser.newContext();
            Page page = context.newPage();

            // 1. Navigate to site
            page.navigate("http://localhost:8000");

            // 2. VERIFY INITIAL STATE (GDPR "Privacy by Default")
            // Replicate in ProB
            trace = trace.execute("VerifyInitialState");
            
            // Replicate in Playwright
            boolean initialCookiesPresent = !context.cookies().isEmpty();
            if (initialCookiesPresent) {
                throw new RuntimeException("GDPR VIOLATION: Cookies found on landing before user interaction!");
            }
            System.out.println("Initial State Verified: No cookies present.");

            // 3. Proceed with Reject flow
            page.click("#reject-btn");
            trace = trace.execute("RejectConsent");
            checkCompliance(context, trace);

            // 4. Reload page to get the cookie banner again
            page.reload();

            // 5. Proceed with Accept flow
            page.click("#accept-btn");
            trace = trace.execute("AcceptConsent");
            checkCompliance(context, trace);
        }
    }


    private static void checkCompliance(BrowserContext context, Trace trace) {
        AbstractEvalResult result = trace.getCurrentState().eval("user_consent_cookie");

        if (result instanceof EvalResult) {
            String machineValue = ((EvalResult) result).getValue();

            boolean cookieExists = context.cookies().stream()
                    .anyMatch(c -> c.name.equals("user_consent"));

            if (machineValue.equals("none") && cookieExists) {
                throw new RuntimeException("GDPR VIOLATION: Model is 'none' but cookie exists!");
            }
            
            System.out.println("Sync Check Passed: Machine=" + machineValue);
        } else {
            throw new RuntimeException("Model Error: Could not evaluate variable.");
        }
    }
}