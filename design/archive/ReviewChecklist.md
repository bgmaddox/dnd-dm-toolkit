dm_toolkit.html Review Checklist
                                                                                                                                                                                                     
  Global Shell    

  - All 6 tabs appear in the top nav (Session, NPC Forge, Scene Painter, Lore Builder, Combat, DM Guide)
  - Claude / Gemini toggle is visible top-right
  - Switching the AI toggle and changing tabs — toggle setting persists
  - Campaign selector (if visible in header) persists across tabs                                                                                                                                    
  - URL hash updates when switching tabs (e.g. #scene, #npc)
  - Browser back/forward navigates between tabs                                                                                                                                                      
                                                                                                                                                                                                     
  State persistence (tab switching)                                                                                                                                                                  
                                                                                                                                                                                                     
  - Type something in NPC Forge → switch to Scene Painter → switch back → text is still there                                                                                                        
  - Same test for Scene Painter → switch away → switch back
  - Same test for Session Companion chat history                                                                                                                                                     
                  
  Per-tool Clear button                                                                                                                                                                              
                  
  - Each tool has a "↺ Clear" button                                                                                                                                                                 
  - Clicking Clear resets that tool's state without affecting other tabs
                                                                                                                                                                                                     
  ---             
  Session Companion                                                                                                                                                                                  
                   
  - Start screen loads — campaign dropdown populated
  - "New Campaign" modal opens, fills in, and creates a campaign                                                                                                                                     
  - Begin Session starts the live view                                                                                                                                                               
  - Resume Session loads previous chat history                                                                                                                                                       
  - Chat send works (type a message, get an AI reply)                                                                                                                                                
  - Prep Mode toggle switches between session chat and prep chat                                                                                                                                     
  - Oracle roll works (select category/race, click Roll)                                                                                                                                             
  - Campaign search returns results                                                                                                                                                                  
  - Finalize Session / log NPC / log Location buttons work                                                                                                                                           
  - Handoff to NPC Forge — "Forge NPC" button in an AI response opens NPC Forge tab with concept pre-filled                                                                                          
  - Handoff to Scene Painter — "Paint Scene" button opens Scene Painter tab with concept pre-filled                                                                                                  
  - Handoff to Combat — "Start Combat" button opens Combat tab                                                                                                                                       
                                                                                                                                                                                                     
  ---                                                                                                                                                                                                
  NPC Forge       
           
  - Concept field required — empty submit shows validation error
  - Random concept button fills the field                                                                                                                                                            
  - Generate NPC returns a result with name, description, voice quirk, etc.                                                                                                                          
  - Generate works with optional fields filled (faction, class, tier, disposition)                                                                                                                   
  - Portrait generates (may take a moment — Pollinations.ai)                                                                                                                                         
  - Save to Campaign saves without error (requires campaign selected)                                                                                                                                
  - Regenerate button works on an existing NPC                                                                                                                                                       
                                                                                                                                                                                                     
  ---                                                                                                                                                                                                
  Scene Painter                                                                                                                                                                                      
                  
  - Location field required — empty submit shows validation error
  - Generate works with only required fields
  - Generate works with optional fields filled (Key Feature, Occupants, Environment) ✓ fixed                                                                                                         
  - Output shows Read Aloud, Details, and DM Note sections                                                                                                                                           
  - Repaint button generates a new scene for the same inputs                                                                                                                                         
  - Save scene to local history works                                                                                                                                                                
  - Saved scenes list appears and can be reloaded                                                                                                                                                    
                                                                                                                                                                                                     
  ---                                                                                                                                                                                                
  Lore Builder    
              
  - NPC and Location tabs switch correctly
  - Form fields accept input                                                                                                                                                                         
  - Save Entity saves to the selected campaign without error
  - Success/error message appears after save                                                                                                                                                         
  - Saved NPC file appears in campaign/<name>/npcs/ on disk                                                                                                                                          
                                                                                                                                                                                                     
  ---                                                                                                                                                                                                
  Combat Companion                                                                                                                                                                                   
                  
  - Initial combatant list renders
  - Add Combatant modal opens — monster search works (type a name)                                                                                                                                   
  - Add PC combatant works                                                                                                                                                                           
  - Add multiple monsters at once works                                                                                                                                                              
  - HP +/- buttons adjust HP; bar color changes (green → yellow → red)                                                                                                                               
  - Next Turn advances the active combatant                                                                                                                                                          
  - Roll Initiatives modal opens, fills in values, applies and sorts the list                                                                                                                        
  - Stat block panel on the right updates when selecting a combatant                                                                                                                                 
  - AI tactics button returns a response                                                                                                                                                             
  - ⚠️  Known no-ops: Save Session button and Encounter Builder button do nothing (not yet implemented)                                                                                               
                                                                                                                                                                                                     
  ---                                                                                                                                                                                                
  DM Learning Guide                                                                                                                                                                                  
                   
  - Content loads — sidebar navigation visible
  - Clicking a sidebar link scrolls to that section                                                                                                                                                  
  - Scrolling the main content highlights the active sidebar link
  - All sections render correctly (headings, tables, lists)                                                                                                                                          
                  
  ---                                                                                                                                                                                                
  After all checks pass
                                                                                                                                                                                                     
  - Commit the branch (feat-spa-merge)
  - Push to GitHub                                                                                                                                                                                   
  - Deploy to Pi: ssh rachett 'bash ~/deploy.sh dnd'                                                                                                                                                 
  - Bump version to 1.2.0 in server.py                                                                                                                                                               
  - Rebuild dist: python scripts/package.py                                                                                                                                                          
  - Commit version bump and dist rebuild                                                                                                                                                             
  - Update USER_GUIDE.md to reference dm_toolkit.html  