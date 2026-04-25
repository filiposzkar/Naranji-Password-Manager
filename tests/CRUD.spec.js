import { test, expect } from '@playwright/test';

const Logins_URL = '/';
const Notes_URL = '/';

// test 1: deleting a login credential
test('delete a login credential', async ({ page }) => {
    await page.goto(Logins_URL);
    page.on('dialog', async dialog => {  // this clicks "OK" when the "Are you sure?" pop up appears 
      await dialog.accept()
    }); 
    await page.locator('.list-item').filter({ hasText: 'Facebook' }).click();  // clicking on the Facebook item
    await page.click('#delete-button');  // clicking the delete button

    const list = page.locator('#credentials_list');  // checking the list of credentials to make sure Facebook is no longer there
    await expect(list).not.toContainText('Facebook', { timeout: 1000 });
});


// test 2: adding a new login credential
test('add new login credential', async ({ page }) => {
    await page.goto(Logins_URL);
    await page.click('#add-item-button');


    await page.fill('#input-website-name', 'GitHub');  // adding a new login credential to the list of credentials
    await page.fill('#display-email', 'ABC@gmail.com');
    await page.fill('#display-username', 'ABC');
    await page.fill('#display-password', '123');
    await page.fill('#display-URL', 'www.github.com');
    await page.click('#save-button');

    const list = page.locator('#credentials_list');   // checking if the list of credentials contains GitHub
    await expect(list).toContainText('GitHub');
});


// test 3: editing an existing login credential
test('edit an existing login credential', async ({ page }) => {
    await page.goto(Logins_URL);
    await page.locator('.list-item').filter({ hasText: 'Figma' }).click();   //clicking on Figma item
    await page.click('#edit-button');
    await page.fill('#input-website-name', 'Figma updated');
    await page.click('text=Save Changes');

    await page.locator('.list-item').filter({ hasText: 'Figma updated' }).click();  // clicking the updated item, so that its content is displayed after the Save Changes button is clicked
    await expect(page.locator('#display-website-name')).toHaveText('Figma updated');

});


test('add new secret note', async ({ page }) => {
    await page.goto('/secretNotes.html');
    await page.click('#add-item-button');

    const nameInput = page.locator('#input-notes-name');
    await nameInput.waitFor({ state: 'visible' });
    await nameInput.fill('Shopping List');
    await page.fill('#display-notes-bodytext', 'Milk, Eggs, Bread');
    
    await page.click('#save-button');
    await expect(page.locator('#notes_list')).toContainText('Shopping List');
});

test('edit an existing secret note', async ({ page }) => {
    await page.goto('/secretNotes.html');
    await page.waitForSelector('.list-item');

    await page.locator('.list-item').filter({ hasText: 'Lecture notes' }).click();
    await page.click('#edit-button');
    await page.fill('#input-notes-name', 'Lecture notes v2');
    await page.fill('#display-notes-bodytext', 'Updated content');
    
    await page.click('text=Save Changes');

    await expect(page.locator('#notes_list')).toContainText('Lecture notes v2');
    await expect(page.locator('#display-notes-name')).toHaveText('Lecture notes v2');
});

test('delete a secret note', async ({ page }) => {
    await page.goto('/secretNotes.html');
    page.on('dialog', async dialog => await dialog.accept());

    await page.waitForSelector('.list-item');
    await page.locator('.list-item').filter({ hasText: 'Project Ideas' }).click();
    await page.click('#delete-button');

    await expect(page.locator('#notes_list')).not.toContainText('Project Ideas');
});

// npx playwright test --headed --workers=1
// npx playwright test --headed