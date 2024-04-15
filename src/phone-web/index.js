import { CallClient } from "@azure/communication-calling";
import { AzureCommunicationTokenCredential } from '@azure/communication-common';

let call;
let incomingCall;
let callAgent;
let deviceManager;
let tokenCredential;
const hangUpButton = document.getElementById("hang-up-button");

document.addEventListener("DOMContentLoaded", async function (event) {
    const callClient = new CallClient();

    // TODO : For production purpose, token needs to be retrieved from backend
    const userTokenCredential = "<ACS_USER_ACCESS_TOKEN>";
    try {
        tokenCredential = new AzureCommunicationTokenCredential(userTokenCredential);
        callAgent = await callClient.createCallAgent(tokenCredential);
        deviceManager = await callClient.getDeviceManager();
        await deviceManager.askDevicePermission({ audio: true });

        hangUpButton.disabled = true;

        // Listen for an incoming call to accept.
        callAgent.on('incomingCall', async (args) => {
            try {
                incomingCall = args.incomingCall;
                console.log(incomingCall);
                call = await incomingCall.accept();
                console.log(call.id);
                hangUpButton.disabled = false;
            } catch (error) {
                console.error(error);
            }
        });
    } catch (error) {
        console.log(error);
        window.alert(error);
    }
});

hangUpButton.addEventListener("click", () => {
    // End the current call
    call.hangUp({ forEveryone: true });
    hangUpButton.disabled = true;
});