---
applyTo: '**'
---
# FamilyHub: GitHub Copilot Development Instructions

## Development Workflow Requirements

### After Each Prompt/Code Generation:

**IMPORTANT: Always Test Before Committing!**

1. **Test Your Changes First**: 
   ```bash
   # Run Django checks
   python manage.py check
   
   # Run database migrations if needed
   python manage.py makemigrations
   python manage.py migrate
   
   # Run development server and test functionality
   python manage.py runserver
   # -> Test the new features in browser to ensure they work
   ```

2. **Commit Changes Only After Testing**: 
   ```bash
   git add .
   git commit -m "Descriptive commit message for what was added/changed"
   ```

3. **Push to GitHub**:
   ```bash
   git push origin main
   ```

4. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```
   **-> Open browser and verify changes work as expected**

**Rule**: Never commit code until you have tested it thoroughly to make sure it really is completed and has no side effects. While committing half-baked things in your local repository only requires you to forgive yourself, having your code tested is even more important when it comes to pushing/sharing your code with others.

### Project Standards

#### Django Conventions:
- Use Django best practices for models, views, and templates
- Follow PEP 8 styling conventions
- Use Django's built-in User model for authentication
- Implement proper form validation
- Use Django's ORM for database operations

#### Code Quality:
- Write clean, readable code with appropriate comments
- Use meaningful variable and function names
- Include docstrings for complex functions
- Handle errors gracefully with try/except blocks

#### Git Commit Message Best Practices:

**Structure**: 
```
<type>(optional scope): <description>

[optional body]

[optional footer]
```

**Types**: feat, fix, docs, style, refactor, test, chore

**The Seven Rules**:
1. **Limit subject line to 50 characters** - Forces you to think concisely
2. **Capitalize only the first letter** - Standard convention
3. **Don't end subject line with period** - Saves space
4. **Use imperative mood** - "Add feature" not "Added feature" or "Adding feature"
5. **Insert blank line between subject and body** - For readability  
6. **Wrap body at 72 characters** - For git log readability
7. **Use body to explain WHAT and WHY, not HOW** - Code shows how, commit explains why

**Imperative Test**: Complete this sentence: "If applied, this commit will ___"
- ✅ "If applied, this commit will **fix the dropdown menu alignment**"
- ❌ "If applied, this commit will **fixed the dropdown menu alignment**"

**Good Examples**:
- `feat: add user authentication system`
- `fix: resolve dropdown menu alignment issue on profile page`
- `refactor: simplify error handling logic`
- `docs: update installation instructions`
- `test: add unit tests for timesheet validation`

**What Makes a Great Commit**:
- **Clear and descriptive**: Someone reading it 6 months later understands what changed
- **Focused**: One logical change per commit
- **Complete**: All related changes included, nothing half-done
- **Tested**: Code works and doesn't break existing functionality

#### Development Testing:
- Test each new feature immediately after implementation
- Run `python manage.py check` before committing
- Verify database migrations work: `python manage.py makemigrations` and `python manage.py migrate`
- Test forms and validation in browser

### Project-Specific Requirements

#### For Timesheet App:
- Focus on Phase 1 MVP features only
- Implement time overlap validation
- Use Bootstrap for quick, clean UI
- Keep it simple and functional
- Ensure mobile-friendly responsive design

#### Database:
- Use SQLite for development (Django default)
- Create proper model relationships
- Include `__str__` methods for all models
- Add appropriate model validation

#### Templates:
- Use Django template inheritance
- Include basic Bootstrap styling
- Create intuitive user interface
- Add form validation feedback

---
**Remember**: Test → Commit → Push → Run Server → Verify in Browser

**Complete Workflow**: Test functionality → Commit working code → Push to GitHub → Run development server → Check in browser that everything works