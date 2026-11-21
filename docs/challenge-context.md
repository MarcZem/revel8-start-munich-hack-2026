# START Munich 2026 Challenge Context — revel8

> Historical context from the 20:30 Voice Memos recording titled “Technische Universität München”. The source recording is in German. The appendix is a machine-generated English translation using Faster Whisper (`small`, German → English); it has not been checked against the audio line by line. The official case and scoring PDFs transcribed in [`revel8-official-challenge.md`](revel8-official-challenge.md) take precedence over this transcript. Its final portion contains low-confidence fragments and timestamps beyond the recording duration.

For later organizer clarifications about scoring touches, form submissions, and `sent_at`, use the dated [November 21 update](revel8-updates-2026-11-21.md) and the current [API guide](revel8-api.md); those details were not in the original recording.

## Executive summary

The challenge is to build a generalizable, agent-driven security simulation that interacts with organizer-provided AI personas through an API. The personas represent people and should be treated as simulated human targets, not as language models to manipulate. The system should use publicly available information to form an understanding of each persona, create context-appropriate interactions, send them through the challenge interface, observe resulting events, and adapt its next step. The final scoring run is expected to use personas beyond the three practice personas, so a system that only memorizes the supplied founders will not generalize.

The organizers emphasize system architecture, persistence, explainability, user-facing interaction rendering, and a clear pitch/demo. They explicitly discourage prompt injection or attempts to bypass the persona agent’s instructions. The recording discusses credential-related events as possible simulated outcomes; the challenge API and its test personas are the stated environment. The API documentation and precise authorization boundaries were not included in the recording.

## Challenge workflow described

1. Research a persona using permitted public information. Organizers mention sources such as LinkedIn, theses, and role-related public material.
2. Develop an evidence-based persona profile and keep track of which observations support it.
3. Generate a contextual interaction using the solution’s chosen communication channel(s).
4. Submit the interaction through the organizer-provided API and capture the returned events.
5. Reassess the run, record what happened, and decide whether to continue or change approach.
6. Present the full interaction trace, including timing, rationale, alternatives considered, and a readable rendering of the messages.

The official case brief lists the supported channel families and says the API renders submitted mail and landing-page artifacts after scoring. The API start-page documentation remains authoritative for exact endpoint and payload schemas.

## Rubric

The audio-only interpretation below has been superseded by the case-page details in [`revel8-official-challenge.md`](revel8-official-challenge.md). The official rubric gives 25 points for Results, 10 for Targeting, 10 for Craft, 40 for Architecture and Persistence, and 15 for Pitch and Demo. See that file for the subscore formulas and tie-breakers.

## Product and architecture expectations

- **Generalize:** support new personas in the final run, rather than hard-coding the three practice founders.
- **Keep an evidence trail:** show the public-source observations behind the profile and the reasoning behind consequential system decisions.
- **Persist and reassess:** track attempts and outcomes; identify when a path is unproductive and choose a justified next step.
- **Make the run legible:** provide a UI with an end-to-end timeline, rendered messages, resulting events, and concise rationale/alternatives.
- **Support rehearsal:** unlimited practice is available against the three founder twins. Local fictional fixtures can test generalization, but do not replace the official practice or scoring API.
- **Keep evaluation in bounds:** the official case brief confirms that practice and scoring targets are AI twins and all interactions stay inside the simulation. Use the supplied challenge API and do not contact real people or use real communication channels.
- **Do not attack the persona model:** organizers explicitly say not to use prompt injection or workarounds to make the agent disclose information it should not. The intended simulation concerns how a person responds to interactions, not how to jailbreak the underlying model.

## Challenge inputs and remaining implementation questions

The official case description is in [`revel8-official-challenge.md`](revel8-official-challenge.md). It confirms three founder AI twins for unlimited practice, new AI-twin targets for scoring, API-based interactions, a ten-touch limit in each of three scoring sessions, the channel list, incident categories, score formulas, and a five-minute pitch.

Remaining implementation questions are operational: exact endpoint schemas and rate limits, sender/channel fields, and the response/event structures. Resolve these from the current API docs before changing the adapter. Session memory, touch accounting, form value handling, and story timestamps are covered by the dated update and API guide.

## Scope and source note

This file records what the audio says as challenge context; the official case brief in [`revel8-official-challenge.md`](revel8-official-challenge.md) defines the current scope. The challenge permits simulated incidents through its API, but does not authorize contacting real people or using real communication channels. The transcript includes offensive examples because they were discussed in the recording; they are not instructions to act outside the simulation.

## English transcript (automatic translation)

The transcript below preserves the speech-recognition output with timestamps. It is lightly formatted only by line breaks. Some wording is clearly misrecognized; use the audio and official challenge documentation to resolve ambiguities. Near the end, the model produces low-confidence fragments and timestamps past the stated 20:30 duration.

[0000.46–0008.46] We have about half an hour now, so we'll give you more details on our presentation and our challenge.
[0008.46–0020.60] Yeah, let's see if you still want to do an after-work.
[0020.60–0023.60] So I mean this, I just already presented to you guys, right?
[0023.60–0032.60] So you first have to research the persona, so you will get three different practice personas who are our three founders.
[0032.60–0042.16] These three guys you will have to kind of practice with.
[0042.16–0047.16] You get like an API key where you can kind of reach them.
[0047.16–0051.16] It's not the real people, but it's a very close impersonation.
[0051.16–0057.16] And you kind of get events back on what they did with the content you sent to them.
[0057.16–0067.16] You have to create the content yourself with your solution for the problem.
[0067.16–0077.16] So it has to have the time of information, create the content and then send it out to that API endpoint.
[0077.16–0084.16] So the third part, this is what probably told me at least, is kind of the most difficult.
[0084.16–0095.16] You will have to really try to think around the corner to get your AI models to do this persistent hacking.
[0095.16–0102.16] We do kind of invite you to look beyond open AI and profits to power it.
[0102.16–0106.16] You can maybe look for China or something or something.
[0106.16–0109.16] You don't have as many guardrails.
[0109.16–0114.16] For this also the AMD kind of computing power that you can use is very useful.
[0114.16–0121.16] And definitely check that out and make sure to kind of put something around that.
[0121.16–0125.16] Then the scoring is also maybe important for you guys.
[0125.16–0135.16] So it's kind of 45% judged by, like automatically, and then 55% judged by the jury, which is, I know, a new jury.
[0135.16–0139.16] Fabian and other guys.
[0139.16–0141.16] 25% is the result.
[0141.16–0146.16] So what kind of events you get back from the API,
[0146.16–0151.16] how much information you get, do you get like your password free or something like that.
[0151.16–0154.16] Then 10% is the targeting.
[0154.16–0159.16] So the OSIN profile you build from kind of show open source intelligence.
[0159.16–0162.16] 10% is also the crafting of it.
[0162.16–0170.16] So there is obviously ways to go around doing prompt engineering and this kind of prompt injection, these kind of tactics.
[0170.16–0172.16] We don't want you to do that.
[0172.16–0176.16] It's supposed to be a simulation of a real attack of a real person.
[0176.16–0183.16] So if you use prompt injection to get the AI to do something it's not supposed to do.
[0183.16–0190.16] This will kind of take away from these 10 points and probably from the jury points as well.
[0190.16–0198.16] Then biggest chunk is the architecture and persistence, which is kind of the tough part to get right.
[0198.16–0202.16] So this will be judged by Fabian from other people.
[0202.16–0206.16] And then 50% is like the pitch and demo, which you do in the end.
[0206.16–0208.16] So you can show us what you did.
[0208.16–0214.16] Show us what your resolution can do.
[0214.16–0220.47] And that will also go into the final points.
[0220.47–0222.47] Yeah, you have the prizes.
[0222.47–0226.47] Maybe I can add one or two things regarding the points.
[0226.47–0228.47] First regarding the craft.
[0228.47–0234.47] The craft really means that how well your mails, for example, or what's an SMS, whatever are formatted.
[0234.47–0241.47] Because that would give it away and it's now obviously if you get a mail formatted email or whatever.
[0241.47–0246.47] This will not be taken into account with the practice personas that you get.
[0246.47–0254.47] Because they are just API endpoints and we don't want to go through all the stress of rendering your mails and your requests.
[0254.47–0260.47] But we will render these touch points for the final scoring runs that you will do.
[0260.47–0270.47] So there we will manually render your message history with these personas to then also evaluate how well these touch points were crafted.
[0270.47–0280.47] So I highly recommend you to also build some kind of internal rendering system so you can double check how it actually looks on your own.
[0280.47–0290.47] Also the UI will be nice so that we can actually understand what your form agents actually decided to do, when and how and why.
[0290.47–0293.47] This is super important in the face of the architecture part.
[0293.47–0297.47] Which brings me to my next point, which is the architecture part.
[0297.47–0300.47] As you can see the five-part largest chunk.
[0300.47–0303.47] That is not without reason.
[0303.47–0308.47] I think everyone can get very far in this challenge in the first couple of hours.
[0308.47–0310.47] With the basic things.
[0310.47–0315.47] But the basic things you will probably end up in some kind of dead end at some point.
[0315.47–0323.47] So the persistence to have this kind of level of persistence as forms of agents like they could be seen in the OpenAI Hugging Place incident.
[0323.47–0329.47] Is really something that is not that straightforward and that's the reason why OpenAI had its research that I'm doing.
[0329.47–0337.47] So I would really recommend you to invest some time into really thinking outside of the box in terms of architecture.
[0337.47–0345.47] We build this kind of system in a generalizable way that is not overfitting on these three personas that we will give to you.
[0345.47–0351.47] Because on the scoring runs we will give you new personas on which your architecture also has to work.
[0351.47–0353.47] Basically.
[0353.47–0355.47] So yeah, don't underestimate that.
[0355.47–0359.47] I think that the first 80% are very straightforward and can be achieved very quickly.
[0359.47–0363.47] But the last 20 is whether we will mine this.
[0363.47–0365.47] So yeah, there's a question.
[0365.47–0368.47] I think it was already answered.
[0368.47–0370.47] But I still want to be sure.
[0370.47–0374.47] So while we are building the model we asked for.
[0374.47–0379.47] While we are building can we create our own persona and test the model before the talk?
[0379.47–0380.47] Sure.
[0380.47–0385.47] This challenge is really meant to be as open-minded or open-ended as possible.
[0385.47–0389.47] Obviously we would ask you not to set out such three people.
[0389.47–0392.47] That would be a bit of a problem.
[0392.47–0398.47] We will provide you with an extensive API docs how our endpoints are configured.
[0398.47–0404.47] You can also create your own personas to test on.
[0404.47–0406.47] What about efficiency?
[0406.47–0408.47] Are there any load tests or something like that?
[0408.47–0412.47] Should we focus also on efficiency points?
[0412.47–0414.47] Not that much.
[0414.47–0421.47] We will see honestly because we also don't know how quickly and if you all will manage to create the personas.
[0421.47–0425.47] So if that is the case then it will also be taken into account as to how many times it took you,
[0425.47–0433.47] how much back and forth it took you to meet or to get to an incident event.
[0433.47–0439.47] And load-wise that's not really important right now.
[0439.47–0441.47] So I have a few questions.
[0441.47–0443.47] So basically if I understood the challenge correctly,
[0443.47–0448.47] realistically you want that we create a form of agents that actually is persona, right?
[0448.47–0450.47] It seems that way.
[0450.47–0455.47] So these personas we will be able to test them?
[0455.47–0459.47] Yes, we will provide them with endpoints for our three founders.
[0459.47–0462.47] They basically have a persona form who they are.
[0462.47–0466.47] So they look like a very extensive context form on them,
[0466.47–0470.47] which is based on everything that you can find on the topic web.
[0470.47–0475.47] So this is also part of the targeting part,
[0475.47–0479.47] that you really leverage agents like open source information.
[0479.47–0484.47] What you can find about them on LinkedIn, on their master thesis or whatever
[0484.47–0490.47] and what their current role might imply that they are very excited about.
[0490.47–0492.47] So this is really something.
[0492.47–0495.47] So do we assume all of the information is given or should we do our own?
[0495.47–0497.47] No, own.
[0497.47–0499.47] Like on LinkedIn.
[0499.47–0502.47] Yeah, LinkedIn is the most straightforward thing,
[0502.47–0507.47] but this is again 80, 80, 80, 20, LinkedIn is probably 80.
[0507.47–0508.47] Okay.
[0508.47–0510.47] Maybe the 20 is the most important.
[0510.47–0513.47] So we need a LinkedIn account for this challenge?
[0513.47–0515.47] Okay, I guess.
[0515.47–0517.47] Okay, thanks.
[0523.47–0527.47] It's all kind of channels, also live interactions,
[0527.47–0530.47] but these things won't be like real voice calls,
[0530.47–0533.47] just counted in the end point as a live interaction.
[0533.47–0536.47] So you can just wrap that before.
[0536.47–0538.47] I'm not sure I understood,
[0538.47–0541.47] but in the persona prompt are all the information about the persona
[0541.47–0544.47] or do we have to look beyond that?
[0544.47–0549.47] The persona prompt, I hope you will not see.
[0549.47–0553.47] We set it up, which is like the very maximum
[0553.47–0556.47] that you can find about them on the open web.
[0556.47–0560.47] Maybe you'll find more than we do, that would be also amazing.
[0560.47–0564.47] Yeah, but the persona prompt is just for us to prompt the agent
[0564.47–0567.47] that you will be interacting with, so they know the context.
[0567.47–0569.47] Okay, okay.
[0569.47–0572.47] Do we care about regular email protections
[0572.47–0575.47] like DNS records, IP reputation or headers,
[0575.47–0578.47] or are we just raising in text?
[0578.47–0581.47] Partially, not that much.
[0581.47–0585.47] What would be nice is to use spoofed domains, for example.
[0585.47–0588.47] Obviously, let's say, for example, Allianz,
[0588.47–0591.47] you cannot use their real domain Allianz for con,
[0591.47–0594.47] because that's just not the domain that you would have access to.
[0594.47–0597.47] But you can also incorporate typosquare the domains,
[0597.47–0600.47] look-alike domains that will also play into the part of
[0600.47–0605.26] graph and results eventually.
[0605.26–0608.26] I'm not outsider to this area,
[0608.26–0611.26] but what is a successful event?
[0611.26–0614.26] Like, I send a patient back and if he thinks
[0614.26–0617.26] if this agent, like the founder, we need to do it,
[0617.26–0619.26] it counts as a...
[0619.26–0621.26] For example, you will get events back,
[0621.26–0624.26] for example, link-opened, password-entered,
[0624.26–0627.26] attachment-opened, whatever.
[0627.26–0630.26] But these are all suggestions,
[0630.26–0633.26] but we also ask you to be, again,
[0633.26–0636.26] creative what other success criteria there might be.
[0636.26–0639.26] We have some defined, but in the end,
[0639.26–0642.26] we ask you why the thing that you accomplish with your run
[0642.26–0645.26] is also an incident that we haven't come to as an incident.
[0645.26–0647.26] We also look at it.
[0647.26–0649.26] And it's everything happens within a platform
[0649.26–0651.26] that you guys offer, right?
[0651.26–0653.26] There will be all the endpoints,
[0653.26–0656.26] you should have the platform and the nice UI as well,
[0656.26–0658.26] so that it's visualized somehow.
[0658.26–0661.26] But we have, like, logs, so we can have full set of questions.
[0661.26–0664.26] What kind of events do you want?
[0664.26–0666.26] Yeah.
[0666.26–0668.26] And how do we communicate with this consumer?
[0668.26–0670.26] Is there a chat?
[0670.26–0672.26] Let's go into the call.
[0672.26–0675.26] And we will provide you with different keys?
[0675.26–0678.26] Like one for email, etc.
[0678.26–0680.26] No, email is...
[0680.26–0682.26] Channel is one, like, you offer.
[0682.26–0684.26] Okay.
[0684.26–0686.26] And then the UI should probably show
[0686.26–0688.26] the trace of the entire interaction.
[0688.26–0691.26] Yes, and for example, the gathering of...
[0691.26–0693.26] Orzens, maybe also some rationale
[0693.26–0697.26] on why your system chose the next step
[0697.26–0699.26] as its next step.
[0699.26–0701.26] What other options there might have been and it discarded.
[0701.26–0704.26] So that's also about for assistance
[0704.26–0707.26] and architecture to have some kind of...
[0707.26–0709.26] Or at least that's what I'm suggesting again.
[0709.26–0711.26] I'm happy to hear new approaches.
[0711.26–0713.26] But you have some kind of reevaluation
[0713.26–0716.26] for the agent to say,
[0716.26–0719.26] well, this kind of attack channel is not burned.
[0719.26–0721.26] It doesn't leave anywhere.
[0721.26–0723.26] Let's try another thing.
[0723.26–0725.26] And that should be visualized somehow.
[0726.26–0731.26] Will your person respond deterministic?
[0731.26–0734.26] Okay, so I'll add an M-based.
[0734.26–0738.26] So then we'll allow some time
[0738.26–0740.26] for the answer to the live presentation
[0740.26–0742.26] for both of them.
[0744.26–0746.26] Yeah.
[0746.26–0748.26] So basically we have to collect incidents
[0748.26–0753.26] and we have to make the reasoning agent
[0753.26–0757.26] who was the scoring basically...
[0757.26–0759.26] Yeah, the scoring...
[0759.26–0761.26] The incident that we collect
[0761.26–0764.26] or the reasoning why it didn't go this far
[0764.26–0767.26] to collect this information?
[0767.26–0770.26] Under results, it's mainly the incidents that we collect.
[0770.26–0774.26] But again, if you think that you have found a way
[0774.26–0777.26] to an incident that we don't count as incident
[0777.26–0779.26] and you can make a case for it,
[0779.26–0781.26] we will also incorporate that in the...
[0781.26–0788.88] We can also collect incidents from future
[0788.88–0793.88] but we can also go into no incident
[0793.88–0796.88] but we can also win the challenge.
[0796.88–0798.88] Yeah, if you can, the case for it...
[0798.88–0800.88] Yeah.
[0800.88–0803.88] And then the rationale part will probably be partially
[0803.88–0806.88] under architecture and persistence,
[0806.88–0809.88] pitch maybe, and targeting.
[0809.88–0814.26] It will pay into it.
[0814.26–0817.26] And we're supposed to retrieve passwords
[0817.26–0819.26] like kind of information
[0819.26–0822.26] or is there further information about type of information?
[0822.26–0824.26] Yeah, I think that we can.
[0824.26–0826.26] I think because these are personas
[0826.26–0828.26] that don't know the passwords.
[0828.26–0830.26] And it shouldn't know.
[0830.26–0832.26] Yeah, let's see.
[0832.26–0836.26] Happy to adjust if there are real passwords.
[0836.26–0838.26] Yeah.
[0838.26–0840.26] So summarized, so we are testing and training
[0840.26–0842.26] with like the free test personas
[0842.26–0844.26] and it's going on against the personas
[0844.26–0846.26] where our agent is to do a research
[0846.26–0848.26] for free in the personas
[0848.26–0850.26] and then run some attack
[0850.26–0852.26] but hopefully we have some results, right?
[0852.26–0855.26] And again, results is like 25%
[0855.26–0858.26] and it would be a nice thing to have
[0858.26–0861.26] but the architecture is the most exciting part
[0861.26–0863.26] for us.
[0863.26–0865.26] How you want to...
[0865.26–0867.26] How you want the system to be
[0867.26–0869.26] commonly represented.
[0869.26–0875.38] Yeah.
[0875.38–0877.38] So I hope not because I find like
[0877.38–0879.38] a wide variety of channels
[0879.38–0881.38] in the endpoint.
[0881.38–0883.38] If you have some that you're missing,
[0883.38–0885.38] I'm happy to add them.
[0885.38–0890.74] But no, we're not limited.
[0890.74–0892.74] And again, part of the challenge is also
[0892.74–0894.74] what Tom already mentioned.
[0894.74–0896.74] We will probably at some point run into issues
[0896.74–0898.74] with safety guardrails.
[0898.74–0900.74] We have GPUs from AMD provided.
[0900.74–0903.74] You can try to run local models
[0903.74–0906.74] self-host them on your laptops.
[0906.74–0908.74] It's all part of the challenge.
[0908.74–0912.74] So there are some correct variables.
[0912.74–0914.74] Any other questions?
[0914.74–0917.74] There are some correct variables.
[0917.74–0920.74] So they are behind a secure guardroils
[0920.74–0924.74] and we need to basically get information
[0924.74–0926.74] through Fission Attacks.
[0926.74–0929.74] Yeah, it's super hard
[0929.74–0931.74] to have one system of agent,
[0931.74–0933.74] so to be an engineer, another agent
[0933.74–0935.74] because the agent is not a human
[0935.74–0937.74] and the social engineer is about right.
[0937.74–0939.74] So I try to configure the personas
[0939.74–0941.74] in a way that they're not as strict
[0941.74–0943.74] as a real agent would have been.
[0943.74–0945.74] If they are too easy to crack
[0945.74–0947.74] or too difficult to crack,
[0947.74–0949.74] I will adjust their comp accordingly.
[0949.74–0951.74] And one more thing,
[0951.74–0953.74] just to kind of clarify it again.
[0953.74–0955.74] These agents that are the personas,
[0955.74–0957.74] they are not supposed to be seen
[0957.74–0959.74] as agents, right?
[0959.74–0961.74] They are supposed to be seen as real people.
[0961.74–0963.74] So we are simulating
[0963.74–0965.74] a tech system that you're building
[0965.74–0967.74] just with agents
[0967.74–0969.74] because we don't want that
[0969.74–0971.74] upon us sitting there for a few days.
[0971.74–0973.74] This is what we want to do.
[0973.74–0975.74] So don't focus on trying
[0975.74–0977.74] to get information from the agent
[0977.74–0979.74] or trying to kind of
[0979.74–0981.74] have some work around
[0981.74–0983.74] so the agent does what you want.
[0983.74–0985.74] Really try to see them
[0985.74–0987.74] as an actual person
[0987.74–0989.74] who responds to all the content
[0989.74–0991.74] that you're sending to them
[0991.74–0993.74] in the event or not.
[0993.74–0995.74] So that's like the whole part.
[0995.74–0997.74] It's not really about hacking the agent
[0997.74–0999.74] it's trying to hack the person.
[0999.74–1001.74] So if
[1001.74–1003.74] people indulge me like,
[1003.74–1005.74] for example, it's a problem
[1005.74–1007.74] that really the agents
[1007.74–1009.74] we simulate the
[1009.74–1011.74] accessing the personas e-mail
[1011.74–1013.74] of how the person is.
[1013.74–1015.74] So that we know is like
[1015.74–1017.74] that.
[1017.74–1019.74] So you want to kind of
[1019.74–1021.74] do it in some way.
[1021.74–1023.74] So if you say you get
[1023.74–1025.74] credentials to an e-mail account
[1025.74–1027.74] this is a breach. So then you breach this agent
[1027.74–1029.74] that's the goal.
[1029.74–1031.74] If we don't type in the password
[1031.74–1033.74] then
[1033.74–1035.74] it's a fail.
[1035.74–1037.74] And we define these
[1037.74–1039.74] breaches or have some suggestions for them
[1039.74–1041.74] but as I said, there might be
[1041.74–1043.74] I'm pretty sure that there are other breaches
[1043.74–1045.74] that we haven't defined.
[1045.74–1047.74] For example, making the agent
[1047.74–1049.74] forward in their e-mail
[1049.74–1051.74] would also be a breach
[1051.74–1053.74] technically. But these are things that we
[1053.74–1055.74] I just came up with
[1055.74–1057.74] but these are things that we haven't
[1057.74–1059.74] yet defined.
[1059.74–1061.74] So there might be
[1061.74–1063.74] runs that you do where you think you
[1063.74–1065.74] actually manage to reach an incident
[1065.74–1067.74] but it isn't counted as an incident
[1067.74–1069.74] and let us know and we will
[1069.74–1074.43] add it in our scoring system.
[1074.43–1076.43] For the scoring run the
[1076.43–1078.43] people who will then be used
[1078.43–1080.43] are also supposedly from red light
[1080.43–1082.43] or is this just some random
[1082.43–1084.43] person could be
[1084.43–1086.43] from the street?
[1086.43–1088.43] It should generalize.
[1088.43–1090.43] Your system should be able to generalize.
[1092.43–1094.43] They will be probably real people
[1094.43–1096.43] so we can compare the awesome part
[1096.43–1098.43] that
[1098.43–1100.43] don't rely on them being from red light.
[1108.43–1110.43] Do consumers have access
[1110.43–1112.43] or do they know what's the time
[1112.43–1114.43] and if they see the difference
[1114.43–1116.43] do they know
[1116.43–1118.43] what's the difference
[1123.02–1125.02] That's a nice thought
[1125.02–1127.02] I'm not sure how it really works
[1127.02–1129.02] but I will
[1129.02–1131.02] Yeah
[1131.02–1133.02] Just
[1133.02–1135.02] I'm going to
[1135.02–1137.02] I'm going to go back
[1137.02–1139.02] to experimenting
[1139.02–1141.02] We have
[1143.02–1145.02] We have these three endpoints
[1145.02–1147.02] where you can test how
[1147.02–1149.02] the main scoring
[1149.02–1151.02] points are
[1151.02–1153.02] designed to create the general
[1153.02–1155.02] so that you can adapt
[1155.02–1157.02] to some reverse or something
[1157.02–1159.02] Yeah
[1161.02–1163.02] Basically
[1163.02–1165.02] And as I said this is our proposal
[1165.02–1167.02] of how to go about this
[1167.02–1169.02] I don't know who has already
[1169.02–1171.02] already built their own personas
[1171.02–1173.02] on them that's a very good project
[1173.02–1179.18] just for work
[1179.18–1189.09] Yeah
[1189.09–1191.09] Yeah
[1191.09–1193.09] So we have these
[1193.09–1195.09] available to customers
[1195.09–1197.09] where the
[1197.09–1199.09] personas can be very first
[1199.09–1201.09] So yeah
[1201.09–1203.09] And maybe for information the next session
[1203.09–1205.09] will be about the product
[1205.09–1207.09] So what's the next session
[1207.09–1209.09] ?
[1209.09–1211.09] ?
[1211.09–1213.09] ?
[1213.09–1220.66] ?
[1220.66–1222.66] ?
[1222.66–1224.66] ?
[1224.66–1228.10] ?
[1228.10–1230.10] ?
[1230.10–1232.10] ?
[1232.10–1234.10] ?
[1234.10–1236.10] ?
[1236.10–1238.10] ?
[1240.10–1242.10] ?
