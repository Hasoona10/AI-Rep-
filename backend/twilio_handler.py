"""
Twilio webhook handlers for phone calls.

DEMO SECTION: Phone Call System
This handles incoming phone calls! When someone calls the restaurant, Twilio sends
a webhook here. The system uses speech-to-text to understand what the customer says,
processes it through the AI (with ML intent classification and RAG), and responds
using text-to-speech. It's a full conversational AI phone system!
"""
from fastapi import Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from .utils.logger import logger
from .stt_tts import transcribe_audio, generate_speech_response
from .call_flow import process_customer_message, clear_conversation
from .reservation_logic import get_reservation_system, ReservationSystem
from .intents import Intent
from datetime import datetime, timedelta


async def handle_incoming_call(request: Request) -> Response:
    """
    Handle incoming Twilio call.
    
    DEMO: This is called when someone calls the restaurant number!
    It greets the customer and starts listening for their input.
    The response is TwiML (Twilio Markup Language) that tells Twilio what to do.
    """
    try:
        # Try to get form data
        try:
            form_data = await request.form()
        except Exception as form_error:
            logger.error(f"Error getting form data: {str(form_error)}")
            raise

        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")

        logger.info(f"Incoming call - SID: {call_sid}, From: {from_number}")

        # Build absolute URL for the action using request headers
        host = request.headers.get("host", "example.trycloudflare.com")
        scheme = "https"  # Cloudflare Tunnel always uses HTTPS
        base_url = f"{scheme}://{host}"
        process_url = f"{base_url}/api/twilio/voice/process"
        logger.info(f"Using action URL: {process_url}")

        # Create TwiML response
        response = VoiceResponse()

        # Greeting (Cedar Garden specific; use a Twilio-supported Polly voice)
        greeting = "Hello! Welcome to Cedar Garden Lebanese Kitchen. How can we help you today?"
        response.say(greeting, voice="Polly.Joanna")
        response.pause(length=1)

        # Gather user input
        gather = Gather(
            input="speech",
            action=process_url,
            method="POST",
            speech_timeout="auto",
            language="en-US",
            hints="reservation, hours, menu, price, address, location, catering, shawarma"
        )
        response.append(gather)

        # If no input, say goodbye and hang up
        response.say(
            "I didn't catch that. Please call back when you're ready. Goodbye!",
            voice="Polly.Joanna",
        )
        response.hangup()

        twiml = str(response)
        logger.info(f"Generated TwiML: {twiml[:200]}...")

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        import traceback
        import sys

        error_trace = traceback.format_exc()

        # Force print to stderr (always visible)
        sys.stderr.write(f"\n{'='*60}\n")
        sys.stderr.write("ERROR in handle_incoming_call:\n")
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.stderr.write(f"Error Type: {type(e).__name__}\n")
        sys.stderr.write("Traceback:\n")
        sys.stderr.write(f"{error_trace}\n")
        sys.stderr.write(f"{'='*60}\n\n")
        sys.stderr.flush()

        # Also print to stdout
        print(f"\n{'='*60}", flush=True)
        print("ERROR in handle_incoming_call:", flush=True)
        print(f"Error: {str(e)}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Traceback:\n{error_trace}", flush=True)
        print(f"{'='*60}\n", flush=True)

        try:
            logger.error(f"Error handling incoming call: {str(e)}\n{error_trace}")
        except Exception as log_err:
            sys.stderr.write(f"Logger also failed: {str(log_err)}\n")
            sys.stderr.flush()

        # Create a simple error response
        response = VoiceResponse()
        response.say(
            "I'm sorry, there was an error. Please try calling again later.",
            voice="Polly.Joanna",
        )
        response.hangup()

        twiml = str(response)
        try:
            logger.info(f"Error TwiML: {twiml}")
        except Exception:
            pass

        return Response(content=twiml, media_type="application/xml")


async def handle_voice_input(request: Request) -> Response:
    """
    Process voice input from Twilio.
    
    DEMO: This processes what the customer said! It takes the speech-to-text result,
    sends it through the AI system (ML intent classification + RAG), and generates
    a response that gets converted back to speech. This is the main conversation loop!
    
    Args:
        request: FastAPI request object (contains the transcribed speech)
        
    Returns:
        TwiML response with generated speech (the AI's response)
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        speech_result = form_data.get("SpeechResult")

        logger.info(f"Processing voice input for call {call_sid}: {speech_result}")

        if not speech_result:
            # If no speech detected, prompt again using the same neural voice
            host = request.headers.get("host", "example.trycloudflare.com")
            scheme = "https"
            base_url = f"{scheme}://{host}"
            process_url = f"{base_url}/api/twilio/voice/process"

            response = VoiceResponse()
            response.say(
                "I didn't catch that. Could you please repeat?",
                voice="Polly.Joanna",
            )
            gather = Gather(
                input="speech",
                action=process_url,
                method="POST",
                speech_timeout="auto",
                language="en-US",
            )
            response.append(gather)
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
        # Process the message
        ai_response = await process_customer_message(
            text=speech_result,
            call_sid=call_sid,
            business_id="restaurant_001"
        )
        
        # Create response
        twiml_response = VoiceResponse()
        
        # Handle reservations specially
        if "reservation" in speech_result.lower() or "book" in speech_result.lower() or "table" in speech_result.lower():
            # Process reservation
            reservation_system = get_reservation_system("restaurant_001")
            reservation_data = reservation_system.parse_reservation_request(speech_result, Intent.RESERVATION)
            
            if reservation_data:
                try:
                    # Parse date and time
                    date_str = reservation_data.get("date")
                    time_str = reservation_data.get("time")
                    party_size = reservation_data.get("party_size", 2)
                    
                    # Combine date and time
                    reservation_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    
                    if reservation_system.check_availability(reservation_datetime, party_size):
                        # Create reservation
                        reservation = reservation_system.create_reservation(
                            customer_name=reservation_data.get("customer_name", "Guest"),
                            customer_phone=form_data.get("From", ""),
                            date=reservation_datetime,
                            party_size=party_size,
                            special_requests=reservation_data.get("special_requests")
                        )
                        
                        ai_response = f"Great! I've confirmed your reservation for {reservation_data.get('party_size', 2)} people on {date_str} at {time_str}. You'll receive a confirmation text shortly. Is there anything else I can help you with?"
                    else:
                        ai_response = f"I'm sorry, but we're fully booked for {date_str} at {time_str}. Would you like to try a different time?"
                        
                except Exception as e:
                    logger.error(f"Error creating reservation: {str(e)}")
                    ai_response = "I had trouble processing your reservation. Could you please provide the date, time, and number of guests again?"
        
        # Speak the response using the same voice as the greeting
        twiml_response.say(ai_response, voice="Polly.Joanna")

        # Continue gathering input
        host = request.headers.get("host", "example.trycloudflare.com")
        scheme = "https"
        base_url = f"{scheme}://{host}"
        process_url = f"{base_url}/api/twilio/voice/process"
        
        gather = Gather(
            input="speech",
            action=process_url,
            method="POST",
            speech_timeout="auto",
            language="en-US"
        )
        twiml_response.append(gather)
        
        # Fallback if no input
        twiml_response.say("Thank you for calling. Have a great day!")
        twiml_response.hangup()
        
        return Response(content=str(twiml_response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing voice input: {str(e)}")
        response = VoiceResponse()
        response.say("I'm sorry, I encountered an error. Please try again.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


async def handle_call_status(request: Request):
    """
    Handle call status updates (e.g., call ended).
    
    Args:
        request: FastAPI request object
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        
        logger.info(f"Call status update - SID: {call_sid}, Status: {call_status}")
        
        if call_status == "completed":
            # Clear conversation state when call ends
            clear_conversation(call_sid)
            
        return Response(content="OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error handling call status: {str(e)}")
        return Response(content="Error", status_code=500)


